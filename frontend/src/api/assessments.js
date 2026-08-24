import client from "./client";

export const createAssessment = (payload) => client.post("/assessments", payload).then((r) => r.data);
export const listAssessmentsForCourse = (courseId) =>
  client.get(`/assessments/course/${courseId}`).then((r) => r.data);
export const getAssessment = (id) => client.get(`/assessments/${id}`).then((r) => r.data);
export const submitAssessment = (id, answers) =>
  client.post(`/assessments/${id}/submit`, { answers }).then((r) => r.data);
export const listSubmissions = (id) => client.get(`/assessments/${id}/submissions`).then((r) => r.data);
