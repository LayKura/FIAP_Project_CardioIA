import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.DEV
    ? (import.meta.env.VITE_API_URL || "http://localhost:5000")
    : "",
  timeout: 60000,
});

export default api;
