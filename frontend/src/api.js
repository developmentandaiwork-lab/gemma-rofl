const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

export function getToken() {
  return localStorage.getItem("auth_token");
}

export function setToken(token) {
  if (token) {
    localStorage.setItem("auth_token", token);
  } else {
    localStorage.removeItem("auth_token");
  }
}

async function request(path, options = {}) {
  const token = getToken();
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });
  if (response.status === 204) {
    return null;
  }

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = data.detail || "Request failed";
    const error = new Error(message);
    error.status = response.status;
    throw error;
  }
  return data;
}

export const api = {
  register: (payload) => request("/api/auth/register", { method: "POST", body: JSON.stringify(payload) }),
  login: (payload) => request("/api/auth/login", { method: "POST", body: JSON.stringify(payload) }),
  me: () => request("/api/auth/me"),
  listChats: () => request("/api/chats"),
  createChat: (payload = {}) => request("/api/chats", { method: "POST", body: JSON.stringify(payload) }),
  getChat: (chatId) => request(`/api/chats/${chatId}`),
  renameChat: (chatId, payload) => request(`/api/chats/${chatId}`, { method: "PATCH", body: JSON.stringify(payload) }),
  deleteChat: (chatId) => request(`/api/chats/${chatId}`, { method: "DELETE" }),
  listMessages: (chatId) => request(`/api/chats/${chatId}/messages`),
  sendMessage: (chatId, message) =>
    request(`/api/chats/${chatId}/messages`, { method: "POST", body: JSON.stringify({ message }) }),
};
