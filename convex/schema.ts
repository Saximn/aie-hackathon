import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

export default defineSchema({
  episodes: defineTable({
    episodeId: v.string(),
    task: v.string(),
    startedAt: v.string(),
    endedAt: v.optional(v.string()),
    status: v.optional(v.string())
  }).index("by_episodeId", ["episodeId"]),

  events: defineTable({
    episodeId: v.string(),
    eventId: v.string(),
    timestamp: v.string(),
    eventType: v.string(),
    cycle: v.number(),
    snapshotId: v.optional(v.union(v.string(), v.null())),
    data: v.any()
  })
    .index("by_episode_timestamp", ["episodeId", "timestamp"])
    .index("by_episode_eventId", ["episodeId", "eventId"]),

  current_state: defineTable({
    episodeId: v.string(),
    snapshotId: v.string(),
    cycle: v.number(),
    goal: v.string(),
    game: v.string(),
    symbolic: v.any(),
    derived: v.any(),
    timestamp: v.string()
  }).index("by_episodeId", ["episodeId"]),

  skills: defineTable({
    episodeId: v.string(),
    name: v.string(),
    goal: v.string(),
    description: v.string(),
    version: v.number(),
    tags: v.array(v.string()),
    code: v.string(),
    createdAt: v.string(),
    lastUsedAt: v.optional(v.union(v.string(), v.null()))
  })
    .index("by_name", ["name"])
    .index("by_episode", ["episodeId"]),

  narration_clips: defineTable({
    episodeId: v.string(),
    clipId: v.string(),
    text: v.string(),
    voiceId: v.optional(v.union(v.string(), v.null())),
    audioUrl: v.optional(v.union(v.string(), v.null())),
    audioPath: v.optional(v.union(v.string(), v.null())),
    durationMs: v.optional(v.union(v.number(), v.null())),
    createdAt: v.string(),
    triggeredBy: v.optional(v.union(v.string(), v.null()))
  }).index("by_episode_createdAt", ["episodeId", "createdAt"]),

  lessons: defineTable({
    episodeId: v.string(),
    lessonId: v.string(),
    summary: v.string(),
    failureType: v.optional(v.union(v.string(), v.null())),
    triggeredByTask: v.string(),
    codeExcerpt: v.optional(v.union(v.string(), v.null())),
    createdAt: v.string()
  }).index("by_episode_createdAt", ["episodeId", "createdAt"])
});
