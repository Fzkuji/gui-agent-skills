#!/bin/bash
# 截屏 + 本地 OCR（macOS Vision framework）
# 用法: ./ocr_screen.sh [截图路径]
# 默认截全屏，也可传入已有截图

IMG="${1:-/tmp/screen_ocr.png}"

if [ -z "$1" ]; then
    screencapture -x "$IMG"
fi

swift - "$IMG" << 'SWIFT'
import Vision
import AppKit

let path = CommandLine.arguments[1]
let url = URL(fileURLWithPath: path)
guard let image = NSImage(contentsOf: url),
      let cgImage = image.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
    print("ERROR: Failed to load image")
    exit(1)
}

let request = VNRecognizeTextRequest()
request.recognitionLevel = .accurate
request.recognitionLanguages = ["zh-Hans", "en"]
request.usesLanguageCorrection = true

let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
try! handler.perform([request])

if let results = request.results {
    for observation in results {
        if let candidate = observation.topCandidates(1).first {
            print(candidate.string)
        }
    }
}
SWIFT
