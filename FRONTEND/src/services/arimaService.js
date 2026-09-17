const API_URL = "http://127.0.0.1:8000/api";


export const getHistorique = async (regionId, maladieId, semaines = 52) => {
  const token = localStorage.getItem("token");

  const dateFin = new Date();
  const dateDebut = new Date();
  dateDebut.setDate(dateDebut.getDate() - (semaines * 7));

  const formatDate = (d) => d.toISOString().split("T")[0];


  const url = `${API_URL}/historique-donnees/?maladie_id=${maladieId}&region_id=${regionId}&date_debut=${formatDate(dateDebut)}&date_fin=${formatDate(dateFin)}`;
  
  console.log(" Appel historique vers :", url);

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
    console.error(" Erreur récupération historique:", error);
    throw error;
  }
};


export const getPrevisionsARIMA = async (regionId, maladieId, horizon) => {
  const token = localStorage.getItem("token");
 
  const url = `${API_URL}/previsions/arima?region_id=${regionId}&maladie_id=${maladieId}&horizon=${horizon}`;

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
    console.error(" Erreur récupération prévisions ARIMA:", error);
    throw error;
  }
};