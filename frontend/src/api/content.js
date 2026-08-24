import client from "./client";

export const importCourseContent = (courseId, payload) =>
  client.post(`/courses/${courseId}/import-content`, payload).then((r) => r.data);

export const getCourseWeeks = (courseId) => client.get(`/courses/${courseId}/weeks`).then((r) => r.data);

export const getCourseQA = (courseId) => client.get(`/courses/${courseId}/qa`).then((r) => r.data);
