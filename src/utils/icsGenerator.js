import { DEFAULT_SOURCES } from '../constants';

export function generateICS(event) {
  const formatICSDate = (date) => {
    return date.toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z';
  };

  const escape = (str) => {
    return str.replace(/[\\,;]/g, '\\$&').replace(/\n/g, '\\n');
  };

  const icsContent = [
    'BEGIN:VCALENDAR',
    'VERSION:2.0',
    'PRODID:-//Melbourne Econ Seminars//EN',
    'CALSCALE:GREGORIAN',
    'BEGIN:VEVENT',
    `UID:${event.uid || Date.now() + '@melb-econ-seminars'}`,
    `DTSTAMP:${formatICSDate(new Date())}`,
    `DTSTART:${formatICSDate(event.start)}`,
    event.end ? `DTEND:${formatICSDate(event.end)}` : '',
    `SUMMARY:${escape(event.summary)}`,
    event.description ? `DESCRIPTION:${escape(event.description)}` : '',
    event.location ? `LOCATION:${escape(event.location)}` : '',
    'END:VEVENT',
    'END:VCALENDAR'
  ].filter(Boolean).join('\r\n');

  return icsContent;
}

export function downloadICS(event) {
  const icsContent = generateICS(event);
  const blob = new Blob([icsContent], { type: 'text/calendar;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `${event.summary.replace(/[^a-z0-9]/gi, '_')}.ics`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

export function getCalendarURL(sourceName) {
  const source = DEFAULT_SOURCES.find(s => s.name === sourceName);
  if (source && source.sourceUrl) {
    return source.sourceUrl;
  }
  return null;
}
