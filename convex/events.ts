import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

export const append = mutation({
  args: {
    episodeId: v.string(),
    id: v.string(),
    timestamp: v.string(),
    eventType: v.string(),
    cycle: v.number(),
    snapshotId: v.optional(v.union(v.string(), v.null())),
    data: v.any()
  },
  handler: async (ctx, args) => {
    return await ctx.db.insert("events", {
      episodeId: args.episodeId,
      eventId: args.id,
      timestamp: args.timestamp,
      eventType: args.eventType,
      cycle: args.cycle,
      snapshotId: args.snapshotId ?? null,
      data: args.data
    });
  }
});

export const byEpisode = query({
  args: {
    episodeId: v.string(),
    limit: v.optional(v.number())
  },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("events")
      .withIndex("by_episode_timestamp", (q) => q.eq("episodeId", args.episodeId))
      .order("desc")
      .take(args.limit ?? 100);
  }
});

export const latestEpisodeId = query({
  args: {},
  handler: async (ctx) => {
    const row = await ctx.db.query("episodes").order("desc").first();
    return row?.episodeId ?? null;
  }
});

export const recent = query({
  args: { limit: v.optional(v.number()) },
  handler: async (ctx, args) => {
    const ep = await ctx.db.query("episodes").order("desc").first();
    if (!ep) return [];
    return await ctx.db
      .query("events")
      .withIndex("by_episode_timestamp", (q) => q.eq("episodeId", ep.episodeId))
      .order("desc")
      .take(args.limit ?? 100);
  }
});
