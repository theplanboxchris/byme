import React, { useState, useEffect } from "react";
import { useSelectedKeywords } from "./SelectedKeywordsContext";
import { useParams } from "react-router-dom";

function GroupPage() {
  const { group_id } = useParams();
  const [group, setGroup] = useState(null);
  const [categories, setCategories] = useState([]);
  const [keywords, setKeywords] = useState([]);
  const [newKeyword, setNewKeyword] = useState("");
  const [newCategory, setNewCategory] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("");
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  // Use context for selected keywords
  const { selectedKeywords, addKeyword, removeKeyword } = useSelectedKeywords();

  // Fetch group details
  useEffect(() => {
    fetch(`http://localhost:9080/groups`)
      .then(res => res.json())
      .then(data => {
        const g = data.find(g => g.id === Number(group_id));
        setGroup(g);
      });
  }, [group_id]);

  // Fetch categories for this group
  useEffect(() => {
    fetch(`http://localhost:9080/categories?group_id=${group_id}`)
      .then(res => res.json())
      .then(data => setCategories(data));
  }, [group_id]);

  // Fetch keywords for selected category only
  useEffect(() => {
    if (selectedCategory) {
      fetch(`http://localhost:9080/groups/${group_id}/categories/${selectedCategory}/keywords`)
        .then(res => res.json())
        .then(data => setKeywords(data));
    } else {
      setKeywords([]);
    }
  }, [selectedCategory, group_id]);

  // Add new category
  const handleAddCategory = async (e) => {
    e.preventDefault();
    setError("");
    const trimmed = newCategory.trim();
    if (!trimmed) {
      setError("Category name cannot be empty.");
      return;
    }
    if (categories.some(c => c.name.toLowerCase() === trimmed.toLowerCase())) {
      setError("Category already exists.");
      return;
    }
    try {
      const res = await fetch(`http://localhost:9080/categories`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: trimmed, group_id: Number(group_id) })
      });
      if (res.ok) {
        setNewCategory("");
        fetch(`http://localhost:9080/categories?group_id=${group_id}`)
          .then(res => res.json())
          .then(data => setCategories(data));
      } else {
        const data = await res.json();
        setError(data.detail || "Failed to add category.");
      }
    } catch {
      setError("Network error.");
    }
  };

  // Add new keyword
  const handleAddKeyword = async (e) => {
    e.preventDefault();
    setError("");
    const trimmed = newKeyword.trim();
    if (!trimmed) {
      setError("Keyword cannot be empty.");
      return;
    }
    if (!selectedCategory) {
      setError("Select a category.");
      return;
    }
    try {
      // Create keyword
      const res = await fetch(`http://localhost:9080/keywords`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ word: trimmed })
      });
      if (res.ok) {
        const keyword = await res.json();
        // Link keyword to group/category
        await fetch(`http://localhost:9080/keyword-group-category`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            keyword_id: keyword.id,
            group_id: Number(group_id),
            category_id: Number(selectedCategory)
          })
        });
        setNewKeyword("");
        fetch(`http://localhost:9080/groups/${group_id}/categories/${selectedCategory}/keywords`)
          .then(res => res.json())
          .then(data => setKeywords(data));
      } else {
        const data = await res.json();
        setError(data.detail || "Failed to add keyword.");
      }
    } catch {
      setError("Network error.");
    }
  };

  // Checkbox handler
  // Checkbox handler: add/remove keyword object to context
  const handleKeywordSelect = (kw) => {
    if (selectedKeywords.some((item) => item.uuid === kw.uuid)) {
      removeKeyword(kw.uuid);
    } else {
      addKeyword({ word: kw.word, uuid: kw.uuid });
    }
  };


  // Debug: log keywords and their uuid
  useEffect(() => {
    console.log('keywords:', keywords);
  }, [keywords]);

  // Filtered keywords
  const filteredKeywords = keywords.filter(kw =>
    kw.word.toLowerCase().includes(search.toLowerCase())
  );

  // BLE transfer logic (rewritten to match sendKeywordsOnce in frontend.js)
  const [transferStatus, setTransferStatus] = useState("");
  const [transferError, setTransferError] = useState("");
  const [transferSuccess, setTransferSuccess] = useState("");
  const [isTransferring, setIsTransferring] = useState(false);

  async function transferKeywordsToDevice() {
    setTransferStatus("");
    setTransferError("");
    setTransferSuccess("");
    if (!navigator.bluetooth) {
      setTransferError("Web Bluetooth API not supported in this browser.");
      return;
    }
    if (!selectedKeywords || selectedKeywords.length === 0) {
      setTransferError("No keywords selected!");
      return;
    }
    setIsTransferring(true);
    try {
      // Use correct UUIDs and device filter
      const SERVICE_UUID = "a07498ca-ad5b-474e-940d-16f1fbe7e8cd";
      const CHARACTERISTIC_UUID = "b07498ca-ad5b-474e-940d-16f1fbe7e8cd";

      // Prepare dictionary of uuid: keyword
      const keywordDict = {};
      selectedKeywords.forEach(kw => {
        keywordDict[kw.uuid || kw.keyword_id] = kw.word;
      });
      const jsonPart = JSON.stringify(keywordDict);
      const eofMarker = "<EOF>";
      const jsonString = jsonPart + eofMarker;
      const encoder = new TextEncoder();
      const fullPayload = encoder.encode(jsonString);

      setTransferStatus("🔍 Searching for NIMI_DEV_ device...");

      // Request and connect to device - match any device starting with NIMI_DEV_
      const device = await navigator.bluetooth.requestDevice({
        filters: [{ namePrefix: "NIMI_DEV_" }],
        optionalServices: [SERVICE_UUID]
      });

      setTransferStatus("🔗 Connecting to device...");
      const server = await device.gatt.connect();
      const service = await server.getPrimaryService(SERVICE_UUID);
      const characteristic = await service.getCharacteristic(CHARACTERISTIC_UUID);

      // Chunked transfer
      const chunkSize = 20;
      const totalChunks = Math.ceil(fullPayload.length / chunkSize);
      let chunksSent = 0;
      setTransferStatus(`📤 Sending ${Object.keys(keywordDict).length} keyword(s) in ${totalChunks} chunks...`);
      for (let i = 0; i < fullPayload.length; i += chunkSize) {
        const chunk = fullPayload.slice(i, i + chunkSize);
        chunksSent++;
        try {
          if (characteristic.writeValueWithoutResponse) {
            await characteristic.writeValueWithoutResponse(chunk);
          } else {
            await characteristic.writeValue(chunk);
          }
          await new Promise(r => setTimeout(r, 300)); // delay between chunks
        } catch (chunkError) {
          setTransferError(`❌ Chunk ${chunksSent} failed: ${chunkError.message}`);
          throw chunkError;
        }
      }
      setTransferStatus(`📤 Payload sent. Waiting for device to save file...`);
      await new Promise(r => setTimeout(r, 5000)); // wait for device to process
      await server.disconnect();
      setTransferSuccess(`✅ Keywords sent successfully! (${Object.keys(keywordDict).length} keywords)`);
      setTransferStatus("");
    } catch (error) {
      setTransferError(`❌ Transfer failed: ${error.message}`);
      setTransferStatus("");
    }
    setIsTransferring(false);
  }

  return (
    <div className="min-h-screen w-full bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-400 flex items-center justify-center py-8">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 w-full max-w-5xl">
        {/* Left column: Heading and text */}
        <div className="flex flex-col justify-center items-center">
          <div className="bg-gradient-to-r from-indigo-700 via-purple-700 to-pink-600 text-white p-7 text-center shadow-md rounded-2xl w-full">
            <h1 className="text-3xl font-extrabold mb-2 tracking-tight drop-shadow">🔗 Keyword Manager</h1>
            <p className="opacity-90 text-base font-medium">Add keywords to your nimi</p>

            {/* Left column: Selected keywords list (cart) */}
            <div className="mt-8 mb-4 p-4 bg-white/80 rounded-xl shadow border border-gray-200">
                {/* Selected keywords list (cart) */}
                <h2 className="text-xl font-bold mb-2 text-indigo-700">Selected Keywords</h2>
                {selectedKeywords.length === 0 ? (
                <div className="text-gray-500">No keywords selected.</div>
                ) : (
                <ul className="divide-y divide-gray-200">
                    {selectedKeywords.map(item => (
                    <li key={item.uuid} className="flex items-center justify-between py-2">
                        <span className="text-base text-gray-800">{item.word}</span>
                        <button
                        className="ml-4 px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600"
                        onClick={() => removeKeyword(item.uuid)}
                        >Remove</button>
                    </li>
                    ))}
                </ul>
                )}
            </div>

            {/* Left column: Transfer keywords button goes here */}
            <button
              className={`mt-4 px-6 py-3 rounded-lg font-semibold shadow transition-colors duration-150 bg-gradient-to-r from-emerald-500 to-emerald-700 text-white hover:from-emerald-600 hover:to-emerald-800 ${selectedKeywords.length === 0 || isTransferring ? 'opacity-50 cursor-not-allowed' : ''}`}
              disabled={selectedKeywords.length === 0 || isTransferring}
              onClick={transferKeywordsToDevice}
            >
              {isTransferring ? "Transferring..." : "Transfer Keywords"}
            </button>
            {/* Transfer status and error messages */}
            {transferStatus && (
              <div className="mt-4 p-3 rounded-xl font-medium text-center shadow bg-blue-100 text-blue-800 border border-blue-300">{transferStatus}</div>
            )}
            {transferError && (
              <div className="mt-4 p-3 rounded-xl font-medium text-center shadow bg-red-100 text-red-800 border border-red-300">{transferError}</div>
            )}
            {transferSuccess && (
              <div className="mt-4 p-3 rounded-xl font-medium text-center shadow bg-green-100 text-green-800 border border-green-300">{transferSuccess}</div>
            )}

          </div>

        </div>
        {/* Right column: Form and keyword list */}
        <div className="max-w-xl w-full mx-auto bg-white/90 rounded-2xl shadow-2xl border border-gray-200 backdrop-blur-lg p-8">
           <h1 className="text-3xl font-extrabold mb-6 text-center text-indigo-700 drop-shadow">Group: {group ? group.name : "..."}</h1>
          {/* Add Category */}
          <form onSubmit={handleAddCategory} className="flex gap-3 mb-6 justify-center">
            <input
              type="text"
              value={newCategory}
              onChange={e => setNewCategory(e.target.value)}
              placeholder="Add new category"
              className="flex-1 min-w-[120px] p-3 border border-gray-300 rounded-lg text-base shadow focus:ring-2 focus:ring-purple-400 focus:outline-none transition"
            />
            <button type="submit" className="p-3 px-6 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg text-base font-semibold whitespace-nowrap shadow hover:scale-105 hover:from-purple-600 hover:to-pink-600 transition-transform duration-150">Add Category</button>
          </form>
          {/* Add Keyword */}
          <form onSubmit={handleAddKeyword} className="flex gap-3 mb-6 justify-center">
            <input
              type="text"
              value={newKeyword}
              onChange={e => setNewKeyword(e.target.value)}
              placeholder="Add new keyword"
              className="flex-1 min-w-[120px] p-3 border border-gray-300 rounded-lg text-base shadow focus:ring-2 focus:ring-pink-400 focus:outline-none transition"
            />
            <select
              value={selectedCategory}
              onChange={e => setSelectedCategory(e.target.value)}
              className="flex-1 min-w-[120px] p-3 border border-gray-300 rounded-lg text-base shadow focus:ring-2 focus:ring-purple-400 focus:outline-none transition"
            >
              <option value="">Select category</option>
              {categories.map(cat => (
                <option key={cat.id} value={cat.id}>{cat.name}</option>
              ))}
            </select>
            <button type="submit" className="p-3 px-6 bg-gradient-to-r from-emerald-500 to-emerald-700 text-white rounded-lg text-base font-semibold whitespace-nowrap shadow hover:scale-105 hover:from-emerald-600 hover:to-emerald-800 transition-transform duration-150">Add Keyword</button>
          </form>
          {/* Error */}
          {error && <div className="bg-red-50 border border-red-400 text-red-700 p-2 rounded-lg mb-4 shadow-sm text-center font-medium">{error}</div>}
          {/* Search/filter keywords */}
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search keywords..."
            className="w-full mb-4 p-3 border border-gray-300 rounded-lg text-base shadow focus:ring-2 focus:ring-indigo-400 focus:outline-none transition"
          />
          {/* Keyword list */}
          <ul className="divide-y divide-gray-200 bg-white rounded-xl shadow-inner">
            {filteredKeywords.length === 0 ? (
              <li className="text-center text-gray-500 py-6">No keywords found.</li>
            ) : (
              filteredKeywords.map(kw => (
                <li key={kw.uuid} className="flex items-center py-4 px-4 hover:bg-gray-50 transition rounded-xl">
                  <label className="flex items-center gap-3 w-full cursor-pointer">
                    <input
                      type="checkbox"
                      checked={selectedKeywords.some(item => item.uuid === kw.uuid)}
                      onChange={() => handleKeywordSelect(kw)}
                      className="form-checkbox h-5 w-5 text-indigo-600 rounded focus:ring-indigo-500"
                    />
                    <span className="text-lg font-medium text-gray-800">{kw.word}</span>
                  </label>
                </li>
              ))
            )}
          </ul>
        </div>
      </div>
    </div>
  );
}

export default GroupPage;
