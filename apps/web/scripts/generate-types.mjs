import { writeFile } from "node:fs/promises";
import openapiTS from "openapi-typescript";

const baseUrl = process.env.API_BASE_URL || process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

const url = `${baseUrl}/openapi.json`;
const types = await openapiTS(url);
await writeFile(new URL("../lib/api-types.ts", import.meta.url), types);
console.log("Generated types from", url);
