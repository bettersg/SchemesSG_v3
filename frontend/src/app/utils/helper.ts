// converts a string which could be an array or a single value into an array
export const parseArrayString = (arrstr: string | string[]| undefined) : string[] | undefined => {
  if (!arrstr || arrstr == '') {
    return undefined
  }
  else if (typeof arrstr === 'string') {
    return [arrstr]
  }
  return arrstr
};

// converts a CSV string or string array into a trimmed string array
// used for multi-value fields: scheme_type, who_is_it_for, what_it_gives
export const toStringArray = (value: string | string[] | undefined): string[] => {
  if (!value) return [];
  if (Array.isArray(value)) return value;
  return value.split(",").map((s) => s.trim()).filter(Boolean);
};