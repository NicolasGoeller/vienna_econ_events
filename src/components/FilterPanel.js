import React from 'react';
import { getSourceColor } from '../utils/colorUtils';

export default function FilterPanel({
  sources,
  selectedSources,
  toggleSource,
  handleSourceDoubleClick,
  allTags,
  selectedTags,
  toggleTag,
  handleTagDoubleClick,
  dateFilter,
  setDateFilter,
  customStartDate,
  setCustomStartDate,
  customEndDate,
  setCustomEndDate,
}) {
  return (
    <div className="mb-6 p-4 bg-gray-50 rounded-lg">
      <div className="mb-2">
        <h3 className="text-sm font-semibold text-gray-700 mb-2">Sources</h3>
        <div className="flex flex-wrap gap-2">
          {sources.map((source) => {
            const colors = getSourceColor(source);
            return (
              <button
                key={source}
                onClick={() => toggleSource(source)}
                onDoubleClick={() => handleSourceDoubleClick(source)}
                className={`px-3 py-1 rounded-full text-sm ${
                  selectedSources.has(source)
                    ? `${colors.bg} ${colors.text}`
                    : 'bg-gray-200 text-gray-500'
                }`}
              >
                {source}
              </button>
            );
          })}
        </div>
      </div>

      <div className="mb-2">
        <h3 className="text-sm font-semibold text-gray-700 mb-2">Tags</h3>
        <div className="flex flex-wrap gap-2">
          {[...allTags].sort().map((tag) => {
            return (
              <button
                key={tag}
                onClick={() => toggleTag(tag)}
                onDoubleClick={() => handleTagDoubleClick(tag)}
                className={`px-3 py-1 rounded-full text-sm ${
                  selectedTags.has(tag)
                    ? 'bg-indigo-100 text-indigo-800'
                    : 'bg-gray-200 text-gray-500'
                }`}
              >
                {tag}
              </button>
            );
          })}
        </div>
      </div>

      <div>
        <h3 className="text-sm font-semibold text-gray-700 mb-2">Date Range</h3>
        <div className="flex flex-wrap gap-2 mb-2">
          <button
            onClick={() => setDateFilter('all')}
            className={`px-3 py-1 rounded ${
              dateFilter === 'all' ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700'
            }`}
          >
            All
          </button>
          <button
            onClick={() => setDateFilter('past')}
            className={`px-3 py-1 rounded ${
              dateFilter === 'past' ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700'
            }`}
          >
            Past
          </button>
          <button
            onClick={() => setDateFilter('upcoming')}
            className={`px-3 py-1 rounded ${
              dateFilter === 'upcoming' ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700'
            }`}
          >
            Upcoming
          </button>
          <button
            onClick={() => setDateFilter('custom')}
            className={`px-3 py-1 rounded ${
              dateFilter === 'custom' ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700'
            }`}
          >
            Custom
          </button>
        </div>

        {dateFilter === 'custom' && (
          <div className="flex gap-2 mt-2">
            <input
              type="date"
              value={customStartDate}
              onChange={(e) => setCustomStartDate(e.target.value)}
              className="px-3 py-1 border border-gray-300 rounded"
              placeholder="Start date"
            />
            <input
              type="date"
              value={customEndDate}
              onChange={(e) => setCustomEndDate(e.target.value)}
              className="px-3 py-1 border border-gray-300 rounded"
              placeholder="End date"
            />
          </div>
        )}
      </div>
    </div>
  );
}
