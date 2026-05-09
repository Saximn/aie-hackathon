import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

export const add = mutation({
  args: {
    episodeId: v.string(),
    id: v.string(),
    summary: v.string(),
    failureType: v.optional(v.union(v.string(), v.null())),
    triggeredByTask: v.string(),
    codeExcerpt: v.optional(v.union(v.string(), v.null())),
    createdAt: v.string()
  },
  handler: async (ctx, args) => {
    return await ctx.db.insert("lessons", {
      episodeId: args.episodeId,
      lessonId: args.id,
      summary: args.summary,
      failureType: args.failureType ?? null,
      triggeredByTask: args.triggeredByTask,
      codeExcerpt: args.codeExcerpt ?? null,
      createdAt: args.createdAt
    });
  }
});

export const recent = query({
  args: { limit: v.optional(v.number()) },
  handler: async (ctx, args) => {
    const ep = await ctx.db.query("episodes").order("desc").first();
    if (!ep) return [];
    return await ctx.db
      .query("lessons")
      .withIndex("by_episode_createdAt", (q) => q.eq("episodeId", ep.episodeId))
      .order("desc")
      .take(args.limit ?? 20);
  }
});
