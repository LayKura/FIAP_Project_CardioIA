
import api from "./api";

export async function checkBackend() {
  const response = await api.get("/api/status");
  return response.data;
}
