import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

export const set = mutation({
  args: {
    episodeId: v.string(),
    snapshotId: v.string(),
    cycle: v.number(),
    goal: v.string(),
    game: v.string(),
    symbolic: v.any(),
    derived: v.any(),
    timestamp: v.string()
  },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("current_state")
      .withIndex("by_episodeId", (q) => q.eq("episodeId", args.episodeId))
      .first();
    if (existing) {
      await ctx.db.patch(existing._id, {
        snapshotId: args.snapshotId,
        cycle: args.cycle,
        goal: args.goal,
        game: args.game,
        symbolic: args.symbolic,
        derived: args.derived,
        timestamp: args.timestamp
      });
      return existing._id;
    }
    return await ctx.db.insert("current_state", args);
  }
});

export const latest = query({
  args: {},
  handler: async (ctx) => {
    const ep = await ctx.db.query("episodes").order("desc").first();
    if (!ep) return null;
    return await ctx.db
      .query("current_state")
      .withIndex("by_episodeId", (q) => q.eq("episodeId", ep.episodeId))
      .first();
  }
});

export const byEpisode = query({
  args: { episodeId: v.string() },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("current_state")
      .withIndex("by_episodeId", (q) => q.eq("episodeId", args.episodeId))
      .first();
  }
});
