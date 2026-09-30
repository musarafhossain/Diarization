import * as path from "node:path";
import { fileURLToPath } from "node:url";
import { DiarizationEngine } from "./DiarizationEngine.ts";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

async function main() {
    const projectRoot = path.resolve(__dirname, "../../..");
    const segments = await DiarizationEngine.diarize({
        audioPath: path.join(projectRoot, "voice", "21a48b5e-fb13-489a-acb9-bd952a28eca0.wav"),
        executablePath: path.join(projectRoot, "dist", "diarize.exe"),
        modelDir: path.join(projectRoot, "dist", "models"),
        outputDir: path.join(projectRoot, "output"),
    });

    // Display segments
    console.log("Segments:", segments);
}

main().catch((err) => {
    console.error("Error:", err.message);
    process.exit(1);
});
