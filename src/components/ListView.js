import React from 'react';
import { getSourceColor } from '../utils/colorUtils';
import { formatDate, formatTime } from '../utils/dateUtils';

export default function ListView({ groupedListEvents, onEventClick }) {
  return (
    <div className="space-y-2">
      {groupedListEvents.map((item, idx) => {
        if (item.type === 'month') {
          return (
            <div key={`month-${idx}`} className="mt-6 mb-3">
              <h2 className="text-xl font-bold text-gray-800 border-b-2 border-gray-300 pb-2">
                {item.label}
              </h2>
            </div>
          );
        } else if (item.type === 'week') {
          return (
            <div key={`week-${idx}`} className="mt-4 mb-2">
              <h3 className="text-lg font-semibold text-gray-700 ml-2">
                {item.label}
              </h3>
            </div>
          );
        } else {
          const event = item.data;
          const colors = getSourceColor(event.source);
          return (
            <div
              key={`event-${event.summary}-${idx}`} // Use a more stable key if possible
              onClick={() => onEventClick(event)}
              className={`p-4 border-l-4 ${colors.border} ${colors.bg} rounded-lg ${colors.hover} cursor-pointer transition-colors`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h3 className="font-semibold text-lg text-gray-800">
                    {event.summary}
                  </h3>
                  <div className="mt-2 space-y-1 text-sm text-gray-600">
                    <div>📅 {formatDate(event.start)}</div>
                    <div>
                      🕐 {formatTime(event.start)}
                      {event.end && ` - ${formatTime(event.end)}`}
                    </div>
                    {event.location && <div>📍 {event.location}</div>}
                  </div>
                </div>
                <span
                  className={`ml-4 px-3 py-1 ${colors.bg} ${colors.text} rounded-full text-sm whitespace-nowrap`}
                >
                  {event.source}
                </span>
              </div>
            </div>
          );
        }
      })}
    </div>
  );
}
