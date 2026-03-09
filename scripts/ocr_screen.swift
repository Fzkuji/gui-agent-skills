// ocr_screen.swift — macOS Vision OCR for screenshots
// Usage: swift ocr_screen.swift [image_path]
// If no path given, captures screen first to /tmp/gui_agent_screen.png

import Vision
import AppKit
import Foundation

let imagePath: String
if CommandLine.arguments.count > 1 {
    imagePath = CommandLine.arguments[1]
} else {
    // Capture screen
    imagePath = "/tmp/gui_agent_screen.png"
    let task = Process()
    task.executableURL = URL(fileURLWithPath: "/usr/sbin/screencapture")
    task.arguments = ["-x", imagePath]
    try! task.run()
    task.waitUntilExit()
}

let url = URL(fileURLWithPath: imagePath)
guard let image = NSImage(contentsOf: url),
      let cgImage = image.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
    print("ERROR: Failed to load image at \(imagePath)")
    exit(1)
}

let request = VNRecognizeTextRequest()
request.recognitionLevel = .accurate
request.recognitionLanguages = ["zh-Hans", "zh-Hant", "en"]
request.usesLanguageCorrection = true

let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
try! handler.perform([request])

if let results = request.results {
    for observation in results {
        if let candidate = observation.topCandidates(1).first {
            let box = observation.boundingBox
            // Output: text | x | y | width | height (normalized 0-1, origin bottom-left)
            print("\(candidate.string)|\(String(format:"%.3f",box.origin.x))|\(String(format:"%.3f",box.origin.y))|\(String(format:"%.3f",box.width))|\(String(format:"%.3f",box.height))")
        }
    }
}
