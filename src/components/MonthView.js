import React from 'react';
import { ChevronLeft, ChevronRight } from './Icons';
import { getSourceColor } from '../utils/colorUtils';
import { getLocalDateKey } from '../utils/dateUtils';

const WEEK_DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

export default function MonthView({
  currentDate,
  navigateMonth,
  getMonthGrid,
  eventsByDate,
  onEventClick,
}) {
  const monthGrid = getMonthGrid(currentDate);

  const gridCols = [0, 1, 2, 3, 4, 5, 6].map((dayOfWeek) => {
    const isWeekend = dayOfWeek === 0 || dayOfWeek === 6;
    if (!isWeekend) return '1fr';

    // Check if this day-of-week column has any events across all weeks
    const hasEvents = monthGrid.some((day) => {
      if (day.getDay() !== dayOfWeek) return false;
      const dateKey = getLocalDateKey(day);
      return (eventsByDate[dateKey] || []).length > 0;
    });

    return hasEvents ? '1fr' : '0.5fr';
  }).join(' ');

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <button
          onClick={() => navigateMonth(-1)}
          className="p-2 hover:bg-gray-100 rounded"
        >
          <ChevronLeft />
        </button>
        <h2 className="text-lg md:text-xl font-bold">
          {currentDate.toLocaleDateString('en-AU', {
            month: 'long',
            year: 'numeric',
          })}
        </h2>
        <button
          onClick={() => navigateMonth(1)}
          className="p-2 hover:bg-gray-100 rounded"
        >
          <ChevronRight />
        </button>
      </div>


          <div
      className="gap-1 md:gap-2"
      style={{
        display: 'grid',
        gridTemplateColumns: gridCols
      }}
    >
        {WEEK_DAYS.map((day) => (
          <div key={day} className="text-center font-semibold text-gray-700 py-1 md:py-2 text-xs md:text-base">
            <span className="md:hidden">{day.slice(0, 1)}</span>
            <span className="hidden md:inline">{day}</span>
          </div>
        ))}

        {monthGrid.map((day, idx) => {
          const dateKey = getLocalDateKey(day);
          const dayEvents = eventsByDate[dateKey] || [];
          const isCurrentMonth = day.getMonth() === currentDate.getMonth();
          const isToday = day.toDateString() === new Date().toDateString();

          return (
            <div
              key={idx}
              className={`min-w-0 min-h-[60px] md:min-h-[100px] p-1 md:p-2 border rounded-lg ${
                !isCurrentMonth
                  ? 'bg-gray-50 text-gray-400'
                  : isToday
                  ? 'bg-blue-50 border-blue-300'
                  : 'bg-white border-gray-200'
              }`}
            >
              <div
                className={`text-xs md:text-sm font-semibold mb-1 ${
                  isToday ? 'text-blue-600' : ''
                }`}
              >
                {day.getDate()}
              </div>
              <div className="space-y-1">
                {dayEvents.slice(0, 3).map((event, eventIdx) => {
                  const colors = getSourceColor(event.source);
                  return (
                    <div
                      key={eventIdx}
                      onClick={() => onEventClick(event)}
                      className={`text-xs p-1 ${colors.bg} rounded truncate ${colors.hover} cursor-pointer`}
                      title={event.summary}
                    >
                      {event.summary}
                    </div>
                  );
                })}
                {dayEvents.length > 3 && (
                  <div className="text-xs text-gray-500 pl-1">
                    +{dayEvents.length - 3} more
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
