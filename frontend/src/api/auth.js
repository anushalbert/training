import client from "./client";

export async function signup({ fullName, email, password, role }) {
  const { data } = await client.post("/auth/signup", {
    full_name: fullName,
    email,
    password,
    role,
  });
  return data;
}

export async function login({ email, password }) {
  const form = new URLSearchParams();
  form.append("username", email);
  form.append("password", password);

  const { data } = await client.post("/auth/login", form, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  return data;
}

export async function fetchCurrentUser() {
  const { data } = await client.get("/auth/me");
  return data;
}
