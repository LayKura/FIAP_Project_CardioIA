import api from "./api";

export async function analyzeECG(file, model = "resnet50", accessToken) {
  const formData = new FormData();
  formData.append("image", file);
  formData.append("model", model);

  const response = await api.post("/api/ecg/analisar", formData, {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });

  return response.data.result ?? response.data;
}
