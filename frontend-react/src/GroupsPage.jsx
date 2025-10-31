import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

function GroupsPage() {
  const [groups, setGroups] = useState([]);
  const [newGroup, setNewGroup] = useState("");
  const [error, setError] = useState("");
  const [filter, setFilter] = useState("");

  // Fetch groups from API
  const fetchGroups = () => {
    fetch('http://localhost:9080/groups')
      .then(res => {
        console.log('API response status:', res.status);
        return res.json();
      })
      .then(data => {
        console.log('API response data:', data);
        setGroups(data);
      })
      .catch(err => {
        console.error('API fetch error:', err);
      });
  };

  useEffect(() => {
    fetchGroups();
  }, []);

  // Add new group
  const handleAddGroup = async (e) => {
    e.preventDefault();
    setError("");
    const trimmed = newGroup.trim();
    if (!trimmed) {
      setError("Group name cannot be empty.");
      return;
    }
    // Check for uniqueness client-side
    if (groups.some(g => g.name.toLowerCase() === trimmed.toLowerCase())) {
      setError("Group already exists.");
      return;
    }
    // POST to API
    try {
      const res = await fetch('http://localhost:9080/groups', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: trimmed })
      });
      if (res.ok) {
        setNewGroup("");
        fetchGroups(); // Refresh list
      } else {
        const data = await res.json();
        setError(data.detail || "Failed to add group.");
      }
    } catch (err) {
      setError("Network error.");
    }
  };

  // Delete group
  const handleDeleteGroup = async (groupId) => {
    setError("");
    if (!window.confirm("Are you sure you want to delete this group?")) return;
    try {
      const res = await fetch(`http://localhost:9080/groups/${groupId}`, {
        method: 'DELETE'
      });
      if (res.ok) {
        fetchGroups();
      } else {
        const data = await res.json();
        setError(data.detail || "Failed to delete group.");
      }
    } catch (err) {
      setError("Network error.");
    }
  };

  // Filtered groups
  const filteredGroups = groups.filter(group =>
    group.name.toLowerCase().includes(filter.toLowerCase())
  );

  return (
    <div className="min-h-screen w-full bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-400 flex items-center justify-center py-8">

        <div class="bg-gradient-to-r from-indigo-700 via-purple-700 to-pink-600 text-white p-7 text-center shadow-md">
            <h1 class="text-3xl font-extrabold mb-2 tracking-tight drop-shadow">🔗 Group picker</h1>
            <p class="opacity-90 text-base font-medium">Find groups that match your interests, or add your own.</p>
        </div>



      <div className="max-w-xl w-full mx-auto bg-white/90 rounded-2xl shadow-2xl border border-gray-200 backdrop-blur-lg p-8">
        <h1 className="text-3xl font-extrabold mb-6 text-center text-indigo-700 drop-shadow">Groups</h1>
        <input
          type="text"
          value={filter}
          onChange={e => setFilter(e.target.value)}
          placeholder="Filter groups..."
          className="w-full mb-4 p-3 border border-gray-300 rounded-lg text-base shadow focus:ring-2 focus:ring-indigo-400 focus:outline-none transition"
        />
        <form onSubmit={handleAddGroup} className="flex gap-3 mb-6 justify-center">
          <input
            type="text"
            value={newGroup}
            onChange={e => setNewGroup(e.target.value)}
            placeholder="Add new group"
            className="flex-1 min-w-[120px] p-3 border border-gray-300 rounded-lg text-base shadow focus:ring-2 focus:ring-pink-400 focus:outline-none transition"
          />
          <button type="submit" className="p-3 px-6 bg-gradient-to-r from-indigo-500 to-pink-500 text-white rounded-lg text-base font-semibold whitespace-nowrap shadow hover:scale-105 hover:from-indigo-600 hover:to-pink-600 transition-transform duration-150">Add Group</button>
        </form>
        {error && <div className="bg-red-50 border border-red-400 text-red-700 p-2 rounded-lg mb-4 shadow-sm text-center font-medium">{error}</div>}
        <ul className="divide-y divide-gray-200 bg-white rounded-xl shadow-inner">
          {filteredGroups.length === 0 ? (
            <li className="text-center text-gray-500 py-6">No groups found.</li>
          ) : (
            filteredGroups.map(group => (
              <li key={group.id} className="flex items-center justify-between py-4 px-4 hover:bg-gray-50 transition rounded-xl">
                <Link to={`/groups/${group.id}`} className="text-lg font-medium text-indigo-700 hover:underline">
                  {group.name}
                </Link>
                <button onClick={() => handleDeleteGroup(group.id)} className="px-4 py-2 bg-gradient-to-r from-pink-100 to-red-200 text-red-700 rounded-lg font-semibold shadow hover:from-pink-200 hover:to-red-300 hover:scale-105 transition-transform duration-150">Delete</button>
              </li>
            ))
          )}
        </ul>
      </div>
    </div>
  );
}

export default GroupsPage;
