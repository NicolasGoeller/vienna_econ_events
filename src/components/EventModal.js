import React from 'react';
import { getSourceColor } from '../utils/colorUtils';
import { formatDate, formatTime } from '../utils/dateUtils';

export default function EventModal({ event, onClose }) {
  const colors = getSourceColor(event.source);

  // This is a bit of a hack to render the "cleaned" text as HTML
  // In a production app, you would use a library like DOMPurify to prevent XSS attacks
  const createMarkup = (htmlString) => {
    return { __html: htmlString };
  };

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <div
          className={`p-6 border-l-8 ${colors.border} overflow-y-auto`}
        >
          <div className="flex justify-between items-start mb-2">
            <h2 className="text-2xl font-bold text-gray-800 flex-1 pr-4">
              {event.summary}
            </h2>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 text-3xl leading-none flex-shrink-0"
            >
              ×
            </button>
          </div>

          <div className="space-y-4">
            <div>
              <h3 className="text-sm font-semibold text-gray-600 mb-1">
                Source
              </h3>
              <span
                className={`inline-block px-3 py-1 ${colors.bg} ${colors.text} rounded-full text-sm`}
              >
                {event.source}
              </span>
            </div>

            <div>
              <h3 className="text-sm font-semibold text-gray-600 mb-1">
                Date & Time
              </h3>
              <div className="text-gray-800">
                <div>📅 {formatDate(event.start)}</div>
                <div>
                  🕐 {formatTime(event.start)}
                  {event.end && ` - ${formatTime(event.end)}`}
                </div>
              </div>
            </div>

            {event.location && (
              <div>
                <h3 className="text-sm font-semibold text-gray-600 mb-1">
                  Location
                </h3>
                <div className="text-gray-800">📍 {event.location}</div>
              </div>
            )}

            {event.description && (
              <div>
                <h3 className="text-sm font-semibold text-gray-600 mb-1">
                  Description
                </h3>
                <div
                  className="text-gray-800 whitespace-pre-wrap max-h-96 overflow-y-auto p-3 bg-gray-50 rounded border border-gray-200"
                  dangerouslySetInnerHTML={createMarkup(event.description)}
                />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
