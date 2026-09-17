const API_URL = "http://127.0.0.1:8000/api";

export const getPrevisionsXGBoost = async (maladieNom, horizon) => {
  const token = localStorage.getItem("token");
  
  const encodedMaladie = encodeURIComponent(maladieNom);
  const url = `${API_URL}/predictions/${encodedMaladie}?horizon=${horizon}`;

  console.log(" Appel prévisions XGBoost vers :", url);

  try {
    const response = await fetch(url, {
      method: "GET",
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Erreur HTTP: ${response.status}`);
    }

    const data = await response.json();
    return data.data || [];
    
  } catch (error) {
    console.error(" Erreur récupération prévisions XGBoost:", error);
    throw error;
  }
};