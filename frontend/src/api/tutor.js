import client from "./client";

export const getTutorMessages = (lessonId) => client.get(`/lessons/${lessonId}/tutor/messages`).then((r) => r.data);

export const sendTutorMessage = (lessonId, message) =>
  client.post(`/lessons/${lessonId}/tutor/chat`, { message }).then((r) => r.data);
