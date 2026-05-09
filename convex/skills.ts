import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

export const upsert = mutation({
  args: {
    episodeId: v.string(),
    name: v.string(),
    goal: v.string(),
    description: v.string(),
    version: v.number(),
    tags: v.array(v.string()),
    code: v.string(),
    createdAt: v.string(),
    lastUsedAt: v.optional(v.union(v.string(), v.null()))
  },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("skills")
      .withIndex("by_name", (q) => q.eq("name", args.name))
      .first();
    if (existing) {
      await ctx.db.patch(existing._id, {
        episodeId: args.episodeId,
        goal: args.goal,
        description: args.description,
        version: Math.max(existing.version, args.version),
        tags: args.tags,
        code: args.code,
        lastUsedAt: args.lastUsedAt ?? null
      });
      return existing._id;
    }
    return await ctx.db.insert("skills", {
      episodeId: args.episodeId,
      name: args.name,
      goal: args.goal,
      description: args.description,
      version: args.version,
      tags: args.tags,
      code: args.code,
      createdAt: args.createdAt,
      lastUsedAt: args.lastUsedAt ?? null
    });
  }
});

export const list = query({
  args: {
    episodeId: v.optional(v.union(v.string(), v.null())),
    limit: v.optional(v.number())
  },
  handler: async (ctx, args) => {
    const limit = Math.min(Math.max(args.limit ?? 100, 1), 500);
    if (args.episodeId) {
      return await ctx.db
        .query("skills")
        .withIndex("by_episode", (q) => q.eq("episodeId", args.episodeId as string))
        .order("desc")
        .take(limit);
    }
    return await ctx.db.query("skills").order("desc").take(limit);
  }
});

export const byName = query({
  args: { name: v.string() },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("skills")
      .withIndex("by_name", (q) => q.eq("name", args.name))
      .first();
  }
});
