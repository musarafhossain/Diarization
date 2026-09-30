import { spawn } from "node:child_process";
import { Buffer } from "node:buffer";
import * as fs from "node:fs";
import * as path from "node:path";

/**
 * A detected speaker turn segment.
 */
export interface DiarizationSegment {
    speaker: string;
    start: number;
    end: number;
}

/**
 * Options for a single diarization run.
 */
export interface DiarizeOptions {
    audioPath: string;
    executablePath: string;
    outputDir: string;
    modelDir: string;
    threshold?: number;
}

/**
 * Modular DiarizationEngine that executes the standalone diarize.exe binary.
 */
export class DiarizationEngine {

    /**
     * Runs offline speaker diarization on the given audio file using diarize.exe.
     *
     * @param options Audio path or options object
     * @returns Array of diarization segments
     */
    public static async diarize(options: DiarizeOptions): Promise<DiarizationSegment[]> {
        const audioPath = path.resolve(options.audioPath);
        if (!fs.existsSync(audioPath)) {
            throw new Error(`Audio file not found: ${audioPath}`);
        }

        const executablePath = path.resolve(options.executablePath);
        if (!fs.existsSync(executablePath)) {
            throw new Error(
                `Executable not found: ${executablePath}. Ensure executable file exists.`
            );
        }

        const modelDir = path.resolve(options.modelDir);
        if (!fs.existsSync(modelDir)) {
            throw new Error(`Model directory not found: ${modelDir}`);
        }

        const outputDir = path.resolve(options.outputDir);
        if (!fs.existsSync(outputDir)) {
            fs.mkdirSync(outputDir, { recursive: true });
        }

        const args = [
            "--audio_path",
            audioPath,
            "--output_dir",
            outputDir,
            "--model_dir",
            modelDir,
        ];

        if (options.threshold !== undefined) {
            args.push("--threshold", String(options.threshold));
        }

        // Run the executable
        await this.runProcess(executablePath, args);

        // Resolve output JSON path: <outputDir>/<baseName>_diarization.json
        const baseName = path.basename(audioPath, path.extname(audioPath));
        const outputJson = path.join(outputDir, `${baseName}_diarization.json`);

        return this.loadResult(outputJson);
    }

    /**
     * Reads and parses an existing diarization JSON file.
     */
    public static loadResult(jsonPath: string): DiarizationSegment[] {
        const fullPath = path.resolve(jsonPath);
        if (!fs.existsSync(fullPath)) {
            throw new Error(`Diarization output file not found: ${fullPath}`);
        }

        const raw = fs.readFileSync(fullPath, "utf-8");
        const parsed = JSON.parse(raw);

        if (!Array.isArray(parsed)) {
            throw new Error(`Invalid JSON in ${fullPath}: expected array of segments.`);
        }

        return parsed.map((item: DiarizationSegment) => ({
            speaker: String(item.speaker),
            start: Number(item.start),
            end: Number(item.end),
        }));
    }

    /**
     * Spawns the executable and captures output.
     */
    private static runProcess(
        command: string,
        args: string[],
    ): Promise<void> {
        return new Promise((resolve, reject) => {
            const child = spawn(command, args, {
                windowsHide: true,
                stdio: ["ignore", "pipe", "pipe"],
            });

            let errorMsg = "";

            child.stderr.on("data", (chunk: Buffer) => {
                const text = chunk.toString("utf-8");
                errorMsg += text;
            });

            child.on("error", (err) => {
                reject(new Error(`Failed to start ${command}: ${err.message}`));
            });

            child.on("close", (code) => {
                if (code === 0) {
                    resolve();
                } else {
                    reject(
                        new Error(`Process exited with code ${code}.${errorMsg ? `\n${errorMsg}` : ""}`)
                    );
                }
            });
        });
    }
}

export default DiarizationEngine;