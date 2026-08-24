import client from "./client";

export const listCourses = () => client.get("/courses").then((r) => r.data);
export const getCourse = (id) => client.get(`/courses/${id}`).then((r) => r.data);
export const createCourse = (payload) => client.post("/courses", payload).then((r) => r.data);
export const updateCourse = (id, payload) => client.patch(`/courses/${id}`, payload).then((r) => r.data);
export const deleteCourse = (id) => client.delete(`/courses/${id}`);
export const enrollInCourse = (id) => client.post(`/courses/${id}/enroll`).then((r) => r.data);
export const myEnrollments = () => client.get("/courses/me/enrollments").then((r) => r.data);

export const listMaterials = (courseId) => client.get(`/courses/${courseId}/materials`).then((r) => r.data);
export const uploadMaterial = (courseId, payload) =>
  client.post(`/courses/${courseId}/materials`, payload).then((r) => r.data);
export const deleteMaterial = (courseId, materialId) =>
  client.delete(`/courses/${courseId}/materials/${materialId}`);

export const submitFeedback = (payload) => client.post("/feedback", payload).then((r) => r.data);
export const listFeedbackForCourse = (courseId) =>
  client.get(`/feedback/course/${courseId}`).then((r) => r.data);

export const listAnnouncements = () => client.get("/announcements").then((r) => r.data);
export const createAnnouncement = (payload) => client.post("/announcements", payload).then((r) => r.data);
export const deleteAnnouncement = (id) => client.delete(`/announcements/${id}`);

export const listTrainers = () => client.get("/users/trainers").then((r) => r.data);
export const myCompetencies = () => client.get("/users/me/competencies").then((r) => r.data);
export const setMyCompetencies = (payload) => client.put("/users/me/competencies", payload).then((r) => r.data);

export const listPendingUsers = () => client.get("/admin/users/pending").then((r) => r.data);
export const listAllUsers = () => client.get("/admin/users").then((r) => r.data);
export const approveUser = (id) => client.patch(`/admin/users/${id}/approve`).then((r) => r.data);
export const deactivateUser = (id) => client.patch(`/admin/users/${id}/deactivate`).then((r) => r.data);
export const getStats = () => client.get("/admin/stats").then((r) => r.data);
export const suggestTrainers = (courseId) =>
  client.get(`/admin/courses/${courseId}/suggest-trainers`).then((r) => r.data);
export const assignTrainer = (courseId, trainerId) =>
  client.patch(`/admin/courses/${courseId}/assign-trainer/${trainerId}`).then((r) => r.data);
