// Offline draft preparation using macOS on-device Translation.
// Outputs are drafts. This program neither approves nor publishes content.
import Foundation
import SwiftUI
import Translation

struct LocalTranslationView: View {
    @State private var message = "Preparing local English drafts…"
    let folder: URL
    let configuration = TranslationSession.Configuration(source: Locale.Language(identifier: "zh-Hans"), target: Locale.Language(identifier: "en"))
    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("FieldToFit · Local English preparation").font(.title2)
            Text("Drafts stay on this device. Review is required before publication.")
            Text(message).textSelection(.enabled)
        }.padding(28).frame(width: 600, height: 200)
        .translationTask(configuration) { session in
            do {
                struct Entry: Decodable { let source:String;let prepared:String;let tokens:[String:String] }
                let input = try JSONDecoder().decode([Entry].self, from: Data(contentsOf: folder.appendingPathComponent("local-prepared.json")))
                let destination=folder.appendingPathComponent("local-static-en.json")
                var output=(try? JSONDecoder().decode([String:String].self,from:Data(contentsOf:destination))) ?? [:]
                for start in stride(from:0,to:input.count,by:20) {
                    let batch=Array(input[start..<min(start+20,input.count)]).filter{output[$0.source]==nil}
                    if batch.isEmpty {continue}
                    let responses=try await session.translations(from:batch.enumerated().map{TranslationSession.Request(sourceText:$0.element.prepared,clientIdentifier:String($0.offset))})
                    for response in responses { if let ident=response.clientIdentifier,let index=Int(ident) {
                        let entry=batch[index];var translated=response.targetText
                        for (token,original) in entry.tokens {translated=translated.replacingOccurrences(of:token,with:original,options:.caseInsensitive)}
                        output[entry.source]=translated
                    } }
                    let data=try JSONEncoder().encode(output)
                    try data.write(to:destination,options:.atomic)
                    message="Prepared \(output.count) / \(input.count) drafts. Not reviewed or published."
                }
                message="Complete: \(output.count) local drafts. Review every field before publication."
            } catch { message="Local preparation stopped: \(error)" }
        }
    }
}
@main struct LocalTranslationApp: App {
    var body: some Scene {
        WindowGroup {
            LocalTranslationView(folder:URL(fileURLWithPath:ProcessInfo.processInfo.environment["FIELDTOFIT_LOCALE_DIR"] ?? FileManager.default.currentDirectoryPath))
        }
    }
}
