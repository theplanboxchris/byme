import React, { createContext, useContext, useState } from "react";

const SelectedKeywordsContext = createContext();

export function SelectedKeywordsProvider({ children }) {
  const [selectedKeywords, setSelectedKeywords] = useState([]); // [{ word, uuid }]

  // Add keyword if not already present
  const addKeyword = (keyword) => {
    setSelectedKeywords((prev) => {
      if (prev.some((item) => item.uuid === keyword.uuid)) return prev;
      return [...prev, keyword];
    });
  };

  // Remove keyword by uuid
  const removeKeyword = (uuid) => {
    setSelectedKeywords((prev) => prev.filter((item) => item.uuid !== uuid));
  };

  // Clear all
  const clearKeywords = () => setSelectedKeywords([]);

  return (
    <SelectedKeywordsContext.Provider value={{ selectedKeywords, addKeyword, removeKeyword, clearKeywords }}>
      {children}
    </SelectedKeywordsContext.Provider>
  );
}

export function useSelectedKeywords() {
  return useContext(SelectedKeywordsContext);
}
