import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

export const start = mutation({
  args: {
    episodeId: v.string(),
    task: v.string(),
    startedAt: v.string()
  },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("episodes")
      .withIndex("by_episodeId", (q) => q.eq("episodeId", args.episodeId))
      .first();
    if (existing) return existing._id;
    return await ctx.db.insert("episodes", {
      episodeId: args.episodeId,
      task: args.task,
      startedAt: args.startedAt,
      status: "running"
    });
  }
});

export const finish = mutation({
  args: {
    episodeId: v.string(),
    endedAt: v.string(),
    status: v.string()
  },
  handler: async (ctx, args) => {
    const row = await ctx.db
      .query("episodes")
      .withIndex("by_episodeId", (q) => q.eq("episodeId", args.episodeId))
      .first();
    if (!row) return null;
    await ctx.db.patch(row._id, { endedAt: args.endedAt, status: args.status });
    return row._id;
  }
});

export const list = query({
  args: { limit: v.optional(v.number()) },
  handler: async (ctx, args) => {
    const rows = await ctx.db.query("episodes").order("desc").take(args.limit ?? 20);
    return rows;
  }
});

export const latest = query({
  args: {},
  handler: async (ctx) => {
    const rows = await ctx.db.query("episodes").order("desc").take(1);
    return rows[0] ?? null;
  }
});
