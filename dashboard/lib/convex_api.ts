// Thin API reference for the dashboard package.
//
// The generated Convex API lives outside this Next.js package at
// ../../convex/_generated/api. Importing that runtime file from here makes
// Next resolve "convex/server" from the repo root instead of dashboard's own
// node_modules, which breaks production builds. anyApi preserves the same
// runtime function-reference behavior while avoiding the cross-package import.
import { anyApi } from "convex/server";

export const api = anyApi;
