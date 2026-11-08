import api from "./api";

export async function analyzeECG(file, model = "resnet50") {
  const formData = new FormData();

  formData.append("image", file);
  formData.append("model", model);

  const response = await api.post("/api/ecg/analisar", formData);

  return response.data.result ?? response.data;
}
