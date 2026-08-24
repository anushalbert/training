import client from "./client";

export const getCourseProgress = (courseId) => client.get(`/courses/${courseId}/progress`).then((r) => r.data);

export const completeLesson = (lessonId) => client.post(`/lessons/${lessonId}/complete`).then((r) => r.data);

export const getWeekQuiz = (courseId, weekNumber) =>
  client.get(`/courses/${courseId}/weeks/${weekNumber}/quiz`).then((r) => r.data);

export const submitWeekQuiz = (courseId, weekNumber, answers) =>
  client.post(`/courses/${courseId}/weeks/${weekNumber}/quiz/submit`, { answers }).then((r) => r.data);

export const listNotes = (lessonId) => client.get(`/lessons/${lessonId}/notes`).then((r) => r.data);

export const createNote = (lessonId, payload) => client.post(`/lessons/${lessonId}/notes`, payload).then((r) => r.data);

export const deleteNote = (noteId) => client.delete(`/notes/${noteId}`);
