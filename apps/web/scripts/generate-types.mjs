import { mkdir, writeFile } from "node:fs/promises";
import openapiTS from "openapi-typescript";

const baseUrl = process.env.API_BASE_URL || process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

const url = `${baseUrl}/openapi.json`;
const types = await openapiTS(url);
const outputUrl = new URL("../src/api/schema.ts", import.meta.url);
await mkdir(new URL("../src/api", import.meta.url), { recursive: true });
await writeFile(outputUrl, types);
console.log("Generated types from", url);
