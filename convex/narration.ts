import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

export const add = mutation({
  args: {
    episodeId: v.string(),
    id: v.string(),
    text: v.string(),
    voiceId: v.optional(v.union(v.string(), v.null())),
    audioUrl: v.optional(v.union(v.string(), v.null())),
    audioPath: v.optional(v.union(v.string(), v.null())),
    durationMs: v.optional(v.union(v.number(), v.null())),
    createdAt: v.string(),
    triggeredBy: v.optional(v.union(v.string(), v.null()))
  },
  handler: async (ctx, args) => {
    return await ctx.db.insert("narration_clips", {
      episodeId: args.episodeId,
      clipId: args.id,
      text: args.text,
      voiceId: args.voiceId ?? null,
      audioUrl: args.audioUrl ?? null,
      audioPath: args.audioPath ?? null,
      durationMs: args.durationMs ?? null,
      createdAt: args.createdAt,
      triggeredBy: args.triggeredBy ?? null
    });
  }
});

export const updateAudio = mutation({
  args: {
    id: v.string(),
    audioUrl: v.optional(v.union(v.string(), v.null())),
    audioPath: v.optional(v.union(v.string(), v.null())),
    durationMs: v.optional(v.union(v.number(), v.null()))
  },
  handler: async (ctx, args) => {
    const row = await ctx.db
      .query("narration_clips")
      .withIndex("by_clipId", (q) => q.eq("clipId", args.id))
      .first();
    if (!row) return null;
    await ctx.db.patch(row._id, {
      audioUrl: args.audioUrl ?? row.audioUrl,
      audioPath: args.audioPath ?? row.audioPath,
      durationMs: args.durationMs ?? row.durationMs
    });
    return row._id;
  }
});

export const latest = query({
  args: { limit: v.optional(v.number()) },
  handler: async (ctx, args) => {
    const ep = await ctx.db.query("episodes").order("desc").first();
    if (!ep) return [];
    return await ctx.db
      .query("narration_clips")
      .withIndex("by_episode_createdAt", (q) => q.eq("episodeId", ep.episodeId))
      .order("desc")
      .take(args.limit ?? 5);
  }
});
