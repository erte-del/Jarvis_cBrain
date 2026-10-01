// JarvisLocation.app: this Mac's location, places nearby and travel times (Apple Maps),
// printed as one line of JSON, then it quits.
// macOS only gives Location to an app bundle, not to Jarvis's Python, so this is one
// (built by scripts/setup_location.sh). The first run shows macOS's "Allow location?" question.
//
//   JarvisLocation                         where am I
//   JarvisLocation search '{"query": "coffee", "near": "Dubai Mall", "radius_m": 3000}'
//   JarvisLocation directions '{"to": "Dubai Mall", "from": "...", "mode": "driving|walking|transit",
//                               "depart_at": ISO 8601, "arrive_by": ISO 8601}'
import CoreLocation
import Foundation
import MapKit

let args = Array(CommandLine.arguments.dropFirst())
let mode = args.first ?? "where"
let params = (args.count > 1 ? try? JSONSerialization.jsonObject(with: Data(args[1].utf8)) : nil) as? [String: Any] ?? [:]

func iso(_ date: Date) -> String {
    let f = ISO8601DateFormatter()
    f.timeZone = .current
    return f.string(from: date)
}

func parseDate(_ key: String) -> Date? {
    guard let s = params[key] as? String else { return nil }
    let f = ISO8601DateFormatter()
    return f.date(from: s) ?? { f.formatOptions = [.withInternetDateTime, .withFractionalSeconds]; return f.date(from: s) }()
}

final class Locator: NSObject, CLLocationManagerDelegate {
    let manager = CLLocationManager()
    var here = CLLocation()

    func start() {
        manager.desiredAccuracy = kCLLocationAccuracyHundredMeters
        manager.delegate = self  // calls locationManagerDidChangeAuthorization right away
    }

    func locationManagerDidChangeAuthorization(_ m: CLLocationManager) {
        switch m.authorizationStatus {
        case .notDetermined: m.requestWhenInUseAuthorization()
        case .denied, .restricted: finish(["error": "denied"])
        default: m.requestLocation()
        }
    }

    func locationManager(_ m: CLLocationManager, didFailWithError error: Error) {
        finish(["error": error.localizedDescription])
    }

    func locationManager(_ m: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        guard let loc = locations.last else { return }
        m.delegate = nil  // once is enough
        here = loc
        switch mode {
        case "search": search()
        case "directions": directions()
        default: whereAmI()
        }
    }

    func whereAmI() {
        var out: [String: Any] = [
            "latitude": here.coordinate.latitude, "longitude": here.coordinate.longitude,
            "accuracy_m": Int(here.horizontalAccuracy),
        ]
        CLGeocoder().reverseGeocodeLocation(here) { places, _ in
            if let p = places?.first {
                out["place"] = [p.name, p.subLocality, p.locality, p.administrativeArea, p.country]
                    .compactMap { $0 }.reduce(into: [String]()) { if !$0.contains($1) { $0.append($1) } }
                    .joined(separator: ", ")
                out["timezone"] = p.timeZone?.identifier
            }
            self.finish(out)
        }
    }

    /// Places matching `query` around `center`, most relevant first.
    func find(_ query: String, around center: CLLocationCoordinate2D, radius: Double,
              done: @escaping ([MKMapItem]) -> Void) {
        let request = MKLocalSearch.Request()
        request.naturalLanguageQuery = query
        request.region = MKCoordinateRegion(center: center, latitudinalMeters: radius * 2, longitudinalMeters: radius * 2)
        MKLocalSearch(request: request).start { response, error in
            guard let items = response?.mapItems, !items.isEmpty else {
                return self.finish(["error": "nothing found for '\(query)'" + (error.map { " (\($0.localizedDescription))" } ?? "")])
            }
            done(items)
        }
    }

    /// One place for a name or address ("Dubai Mall", "home address"), or here if it's empty.
    func place(_ text: String?, done: @escaping (MKMapItem) -> Void) {
        guard let text = text, !text.isEmpty else {
            let item = MKMapItem(placemark: MKPlacemark(coordinate: here.coordinate))
            item.name = "Current location"
            return done(item)
        }
        find(text, around: here.coordinate, radius: 50_000) { done($0[0]) }
    }

    func distance(_ item: MKMapItem, from c: CLLocationCoordinate2D) -> Double {
        let p = item.placemark.coordinate
        return CLLocation(latitude: p.latitude, longitude: p.longitude).distance(from: CLLocation(latitude: c.latitude, longitude: c.longitude))
    }

    func describe(_ item: MKMapItem) -> [String: Any] {
        let p = item.placemark
        var d: [String: Any] = [
            "name": item.name ?? "", "latitude": p.coordinate.latitude, "longitude": p.coordinate.longitude,
            "distance_m": Int(distance(item, from: here.coordinate)),  // from the user
        ]
        if item.name != "Current location", let address = p.title { d["address"] = address }
        if let phone = item.phoneNumber { d["phone"] = phone }
        if let url = item.url { d["url"] = url.absoluteString }
        if let c = item.pointOfInterestCategory { d["category"] = c.rawValue.replacingOccurrences(of: "MKPOICategory", with: "") }
        return d
    }

    func search() {
        let query = params["query"] as? String ?? ""
        let radius = params["radius_m"] as? Double ?? 5_000
        place(params["near"] as? String) { center in
            let c = center.placemark.coordinate
            self.find(query, around: c, radius: radius) { items in
                // Nearest first; Apple's own order is relevance, which can put the far side of town first.
                let sorted = items.sorted { self.distance($0, from: c) < self.distance($1, from: c) }
                let inside = sorted.filter { self.distance($0, from: c) <= radius }
                self.finish(["near": self.describe(center), "places": (inside.isEmpty ? sorted : inside).prefix(10).map(self.describe)])
            }
        }
    }

    func directions() {
        let how = params["mode"] as? String ?? "driving"
        place(params["from"] as? String) { from in
            self.place(params["to"] as? String ?? "") { to in
                let request = MKDirections.Request()
                request.source = from
                request.destination = to
                request.transportType = ["walking": .walking, "transit": .transit][how] ?? .automobile
                if let at = parseDate("arrive_by") { request.arrivalDate = at }
                else { request.departureDate = parseDate("depart_at") ?? Date() }  // now = live traffic
                MKDirections(request: request).calculateETA { eta, error in
                    guard let eta = eta else {
                        return self.finish(["error": "no \(how) route: \(error?.localizedDescription ?? "unknown")"])
                    }
                    let a = from.placemark.coordinate, b = to.placemark.coordinate
                    let flag = ["walking": "w", "transit": "r"][how] ?? "d"
                    self.finish([
                        "from": self.describe(from), "to": self.describe(to), "mode": how,
                        "minutes": Int((eta.expectedTravelTime / 60).rounded()),
                        "distance_km": (eta.distance / 100).rounded() / 10,
                        "depart": iso(eta.expectedDepartureDate), "arrive": iso(eta.expectedArrivalDate),
                        "maps_url": "https://maps.apple.com/?saddr=\(a.latitude),\(a.longitude)&daddr=\(b.latitude),\(b.longitude)&dirflg=\(flag)",
                    ])
                }
            }
        }
    }

    func finish(_ out: [String: Any]) {
        FileHandle.standardOutput.write(try! JSONSerialization.data(withJSONObject: out))
        exit(0)
    }
}

let locator = Locator()
locator.start()
// Long enough to answer macOS's question the first time.
DispatchQueue.main.asyncAfter(deadline: .now() + 120) { locator.finish(["error": "timeout"]) }
RunLoop.main.run()
