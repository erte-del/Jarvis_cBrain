// JarvisLocation.app: prints this Mac's location as one line of JSON, then quits.
// macOS only gives Location to an app bundle, not to Jarvis's Python, so this is one
// (built by scripts/setup_location.sh). The first run shows macOS's "Allow location?" question.
import CoreLocation
import Foundation

final class Locator: NSObject, CLLocationManagerDelegate {
    let manager = CLLocationManager()

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

    func locationManager(_ m: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        guard let loc = locations.last else { return }
        var out: [String: Any] = [
            "latitude": loc.coordinate.latitude, "longitude": loc.coordinate.longitude,
            "accuracy_m": Int(loc.horizontalAccuracy),
        ]
        CLGeocoder().reverseGeocodeLocation(loc) { places, _ in
            if let p = places?.first {
                out["place"] = [p.name, p.subLocality, p.locality, p.administrativeArea, p.country]
                    .compactMap { $0 }.reduce(into: [String]()) { if !$0.contains($1) { $0.append($1) } }
                    .joined(separator: ", ")
                out["timezone"] = p.timeZone?.identifier
            }
            self.finish(out)
        }
    }

    func locationManager(_ m: CLLocationManager, didFailWithError error: Error) {
        finish(["error": error.localizedDescription])
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
