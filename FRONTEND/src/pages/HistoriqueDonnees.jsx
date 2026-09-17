import React, { useState, useEffect, useRef } from "react";
import { History, Filter, Download, Calendar, MapPin, Activity, ChevronDown, X } from "lucide-react";

export default function HistoriqueDonnees() {

  const API_URL = "/api/historique-donnees";

  const [maladies, setMaladies] = useState([]);
  const [regions, setRegions] = useState([]);
  const [data, setData] = useState([]);
  const [statistics, setStatistics] = useState(null);
  const [loading, setLoading] = useState(false);

 
  const [filterMaladie, setFilterMaladie] = useState("");
  const [filterRegion, setFilterRegion] = useState("");
  const [filterDateDebut, setFilterDateDebut] = useState("");
  const [filterDateFin, setFilterDateFin] = useState("");

 
  const [searchMaladie, setSearchMaladie] = useState("");
  const [searchRegion, setSearchRegion] = useState("");
  const [isMaladieDropdownOpen, setIsMaladieDropdownOpen] = useState(false);
  const [isRegionDropdownOpen, setIsRegionDropdownOpen] = useState(false);
  
  
  const maladieDropdownRef = useRef(null);
  const regionDropdownRef = useRef(null);

  useEffect(() => {
    fetchMaladies();
    fetchRegions();
  }, []);

  
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (maladieDropdownRef.current && !maladieDropdownRef.current.contains(event.target)) {
        setIsMaladieDropdownOpen(false);
        setSearchMaladie("");
      }
      if (regionDropdownRef.current && !regionDropdownRef.current.contains(event.target)) {
        setIsRegionDropdownOpen(false);
        setSearchRegion("");
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const fetchMaladies = async () => {
    try {
      const token = localStorage.getItem("token");
      if (!token) return;

      const response = await fetch(`${API_URL}/maladies`, {
        headers: { "Authorization": `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setMaladies(data);
      }
    } catch (error) {
      console.error("Erreur fetchMaladies:", error);
    }
  };

  const fetchRegions = async () => {
    try {
      const token = localStorage.getItem("token");
      if (!token) return;

      const response = await fetch(`${API_URL}/regions`, {
        headers: { "Authorization": `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setRegions(data);
      }
    } catch (error) {
      console.error("Erreur fetchRegions:", error);
    }
  };

  const handleRechercher = async () => {
    if (!filterMaladie || !filterRegion) {
      alert("Veuillez sélectionner au moins une maladie et une région.");
      return;
    }

    setLoading(true);
    setData([]);
    setStatistics(null);

    try {
      const token = localStorage.getItem("token");
      if (!token || token === "null" || token === "undefined") {
        alert("Session expirée. Veuillez vous reconnecter.");
        window.location.href = "/login";
        return;
      }

      const params = new URLSearchParams();
      params.append("maladie_id", filterMaladie);
      params.append("region_id", filterRegion);
      if (filterDateDebut) params.append("date_debut", filterDateDebut);
      if (filterDateFin) params.append("date_fin", filterDateFin);

      const url = `${API_URL}/?${params.toString()}`;
      console.log(" Appel API vers :", url);

      const response = await fetch(url, {
        method: "GET",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json"
        }
      });

      if (response.status === 401) {
        alert("Session expirée. Veuillez vous reconnecter.");
        localStorage.removeItem("token");
        localStorage.removeItem("user");
        window.location.href = "/login";
        return;
      }

      if (response.ok) {
        const result = await response.json();
        console.log(" Données reçues :", result);

        setData(result.data || []);
        setStatistics(result.statistics || null);
      } else {
        const errorText = await response.text();
        console.error(" Erreur backend :", response.status, errorText);
        alert("Erreur lors de la récupération des données.");
      }
    } catch (error) {
      console.error(" Exception fetch :", error);
      alert("Erreur de connexion : " + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setFilterMaladie("");
    setFilterRegion("");
    setFilterDateDebut("");
    setFilterDateFin("");
    setData([]);
    setStatistics(null);
    setSearchMaladie("");
    setSearchRegion("");
  };

  const handleExportCSV = () => {
    if (data.length === 0) return;

    const headers = "Date,Région,Cas nouveaux,Décès,Guéris,Hospitalisations,Taux incidence,Taux létalité,Niveau alerte\n";
    const rows = data.map(item =>
      `${item.date},${item.region_nom || ""},${item.cas_nouveaux},${item.deces},${item.gueris},${item.hospitalisations || 0},${item.taux_incidence || 0},${item.taux_letalite || 0},${item.niveau_alerte || "Faible"}`
    ).join("\n");

    const csvContent = headers + rows;
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `historique_${filterMaladie}_${Date.now()}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };


  const maladiesFiltrees = maladies.filter(m => 
    (m.nom_officiel || m.nom || "").toLowerCase().includes(searchMaladie.toLowerCase())
  ).slice(0, 4);

  const regionsFiltrees = regions.filter(r => 
    (r.nom_region || r.nom || "").toLowerCase().includes(searchRegion.toLowerCase())
  ).slice(0, 4);

  
  const selectedMaladieText = maladies.find(m => m.id === filterMaladie)?.nom_officiel || 
                               maladies.find(m => m.id === filterMaladie)?.nom || 
                               "";
  const selectedRegionText = regions.find(r => r.id === filterRegion)?.nom_region || 
                              regions.find(r => r.id === filterRegion)?.nom || 
                              "";

  return (
    <div className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8 space-y-6 w-full relative z-10 bg-gray-50 min-h-screen">

      {/* En-tête */}
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold text-slate-800 flex items-center gap-3">
          <History className="w-8 h-8 text-emerald-600" />
          Historique des Données Épidémiologiques
        </h1>
        <p className="text-slate-500 mt-1">
          Consultez l'historique des cas par maladie, région et période
        </p>
      </div>

      {/* Filtres */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
        <h2 className="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2">
          <Filter className="w-5 h-5 text-emerald-600" />
          Filtres de recherche
        </h2>

        <div className="grid md:grid-cols-4 gap-4">

          {/* Maladie avec Recherche */}
          <div ref={maladieDropdownRef} className="relative">
            <label className="block text-sm font-medium text-slate-700 mb-2">
              <Activity className="w-4 h-4 inline mr-1" />
              Maladie
            </label>
            <div className="relative">
              <input
                type="text"
                value={isMaladieDropdownOpen ? searchMaladie : selectedMaladieText}
                onChange={(e) => {
                  setSearchMaladie(e.target.value);
                  setIsMaladieDropdownOpen(true);
                }}
                onFocus={() => setIsMaladieDropdownOpen(true)}
                placeholder="Rechercher une maladie..."
                className="w-full px-4 py-2.5 border border-slate-200 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none pr-10"
                readOnly={!isMaladieDropdownOpen}
              />
              <button
                type="button"
                onClick={() => {
                  if (filterMaladie) {
                    setFilterMaladie("");
                    setSearchMaladie("");
                  } else {
                    setIsMaladieDropdownOpen(true);
                  }
                }}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
              >
                {filterMaladie && !isMaladieDropdownOpen ? (
                  <X className="w-4 h-4" />
                ) : (
                  <ChevronDown className="w-4 h-4" />
                )}
              </button>
            </div>
            
            {/* Dropdown Maladie */}
            {isMaladieDropdownOpen && (
              <div className="absolute z-30 w-full mt-1 bg-white border border-slate-200 rounded-lg shadow-lg max-h-48 overflow-y-auto">
                {maladiesFiltrees.length > 0 ? (
                  maladiesFiltrees.map((m) => (
                    <div
                      key={m.id}
                      onClick={() => {
                        setFilterMaladie(m.id);
                        setSearchMaladie("");
                        setIsMaladieDropdownOpen(false);
                      }}
                      className={`px-4 py-2.5 cursor-pointer text-sm font-medium border-b border-slate-100 last:border-0 transition-colors ${
                        m.id === filterMaladie 
                          ? "bg-emerald-50 text-emerald-700" 
                          : "text-slate-700 hover:bg-emerald-50"
                      }`}
                    >
                      {m.nom_officiel || m.nom}
                    </div>
                  ))
                ) : (
                  <div className="px-4 py-2.5 text-sm text-slate-400">
                    Aucune maladie trouvée
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Région avec Recherche */}
          <div ref={regionDropdownRef} className="relative">
            <label className="block text-sm font-medium text-slate-700 mb-2">
              <MapPin className="w-4 h-4 inline mr-1" />
              Région
            </label>
            <div className="relative">
              <input
                type="text"
                value={isRegionDropdownOpen ? searchRegion : selectedRegionText}
                onChange={(e) => {
                  setSearchRegion(e.target.value);
                  setIsRegionDropdownOpen(true);
                }}
                onFocus={() => setIsRegionDropdownOpen(true)}
                placeholder="Rechercher une région..."
                className="w-full px-4 py-2.5 border border-slate-200 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none pr-10"
                readOnly={!isRegionDropdownOpen}
              />
              <button
                type="button"
                onClick={() => {
                  if (filterRegion) {
                    setFilterRegion("");
                    setSearchRegion("");
                  } else {
                    setIsRegionDropdownOpen(true);
                  }
                }}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
              >
                {filterRegion && !isRegionDropdownOpen ? (
                  <X className="w-4 h-4" />
                ) : (
                  <ChevronDown className="w-4 h-4" />
                )}
              </button>
            </div>
            
            {/* Dropdown Région */}
            {isRegionDropdownOpen && (
              <div className="absolute z-30 w-full mt-1 bg-white border border-slate-200 rounded-lg shadow-lg max-h-48 overflow-y-auto">
                {regionsFiltrees.length > 0 ? (
                  regionsFiltrees.map((r) => (
                    <div
                      key={r.id}
                      onClick={() => {
                        setFilterRegion(r.id);
                        setSearchRegion("");
                        setIsRegionDropdownOpen(false);
                      }}
                      className={`px-4 py-2.5 cursor-pointer text-sm font-medium border-b border-slate-100 last:border-0 transition-colors ${
                        r.id === filterRegion 
                          ? "bg-emerald-50 text-emerald-700" 
                          : "text-slate-700 hover:bg-emerald-50"
                      }`}
                    >
                      {r.nom_region || r.nom}
                    </div>
                  ))
                ) : (
                  <div className="px-4 py-2.5 text-sm text-slate-400">
                    Aucune région trouvée
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Date début */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              <Calendar className="w-4 h-4 inline mr-1" />
              Date début
            </label>
            <input
              type="date"
              value={filterDateDebut}
              onChange={(e) => setFilterDateDebut(e.target.value)}
              className="w-full px-4 py-2.5 border border-slate-200 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none"
            />
          </div>

          {/* Date fin */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              <Calendar className="w-4 h-4 inline mr-1" />
              Date fin
            </label>
            <input
              type="date"
              value={filterDateFin}
              onChange={(e) => setFilterDateFin(e.target.value)}
              className="w-full px-4 py-2.5 border border-slate-200 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none"
            />
          </div>
        </div>

        {/* Boutons */}
        <div className="flex gap-3 mt-6">
          <button
            onClick={handleRechercher}
            disabled={loading}
            className="px-6 py-2.5 bg-emerald-600 text-white font-semibold rounded-lg hover:bg-emerald-700 transition-colors disabled:opacity-50 flex items-center gap-2"
          >
            {loading ? "Recherche..." : "Rechercher"}
          </button>
          <button
            onClick={handleReset}
            className="px-6 py-2.5 bg-slate-100 text-slate-700 font-semibold rounded-lg hover:bg-slate-200 transition-colors"
          >
            Réinitialiser
          </button>
        </div>
      </div>

      {/* Statistiques */}
      {statistics && (
        <div className="grid md:grid-cols-4 gap-4">
          <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm">
            <p className="text-sm text-slate-500 mb-1">Total des cas</p>
            <p className="text-2xl font-bold text-emerald-600">{statistics.total_cas.toLocaleString()}</p>
          </div>
          <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm">
            <p className="text-sm text-slate-500 mb-1">Décès</p>
            <p className="text-2xl font-bold text-red-600">{statistics.total_deces.toLocaleString()}</p>
          </div>
          <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm">
            <p className="text-sm text-slate-500 mb-1">Guéris</p>
            <p className="text-2xl font-bold text-blue-600">{statistics.total_gueris.toLocaleString()}</p>
          </div>
          <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm">
            <p className="text-sm text-slate-500 mb-1">Hospitalisations</p>
            <p className="text-2xl font-bold text-orange-600">{statistics.total_hospitalisations.toLocaleString()}</p>
          </div>
        </div>
      )}

      {/* Tableau de résultats */}
      {data.length > 0 && (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="p-6 border-b border-slate-200 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-bold text-slate-800">Résultats</h2>
              <p className="text-sm text-slate-500 mt-1">
                {data.length} ligne{data.length > 1 ? "s" : ""} trouvée{data.length > 1 ? "s" : ""}
              </p>
            </div>
            <button
              onClick={handleExportCSV}
              className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors flex items-center gap-2 text-sm font-medium"
            >
              <Download className="w-4 h-4" />
              Exporter CSV
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200">
                  <th className="px-6 py-3 text-xs font-bold text-slate-600 uppercase">Date</th>
                  <th className="px-6 py-3 text-xs font-bold text-slate-600 uppercase">Région</th>
                  <th className="px-6 py-3 text-xs font-bold text-slate-600 uppercase">Cas</th>
                  <th className="px-6 py-3 text-xs font-bold text-slate-600 uppercase">Décès</th>
                  <th className="px-6 py-3 text-xs font-bold text-slate-600 uppercase">Guéris</th>
                  <th className="px-6 py-3 text-xs font-bold text-slate-600 uppercase">Hospitalisés</th>
                  <th className="px-6 py-3 text-xs font-bold text-slate-600 uppercase">Alerte</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {data.map((item, index) => (
                  <tr key={index} className="hover:bg-slate-50 transition-colors">
                    <td className="px-6 py-4 text-sm text-slate-600">
                      {new Date(item.date).toLocaleDateString('fr-FR')}
                    </td>
                    <td className="px-6 py-4 text-sm font-medium text-slate-800">{item.region_nom || "-"}</td>
                    <td className="px-6 py-4 text-sm text-slate-600">{item.cas_nouveaux}</td>
                    <td className="px-6 py-4 text-sm text-red-600 font-medium">{item.deces}</td>
                    <td className="px-6 py-4 text-sm text-blue-600">{item.gueris}</td>
                    <td className="px-6 py-4 text-sm text-orange-600">{item.hospitalisations || 0}</td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 rounded text-xs font-bold ${
                        item.niveau_alerte === "Critique" ? "bg-red-100 text-red-700" :
                        item.niveau_alerte === "Élevé" ? "bg-orange-100 text-orange-700" :
                        item.niveau_alerte === "Modéré" ? "bg-yellow-100 text-yellow-700" :
                        "bg-green-100 text-green-700"
                      }`}>
                        {item.niveau_alerte || "Faible"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Message si aucun résultat */}
      {data.length === 0 && !loading && (
        <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center">
          <History className="w-16 h-16 text-slate-300 mx-auto mb-4" />
          <p className="text-slate-500 text-lg">Aucune donnée trouvée</p>
          <p className="text-slate-400 text-sm mt-2">Utilisez les filtres ci-dessus pour rechercher des données</p>
        </div>
      )}
    </div>
  );
}