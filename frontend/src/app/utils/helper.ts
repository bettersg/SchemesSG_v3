// converts a string which could be an array or a single value into an array
export const parseArrayString= (arrstr: string) => {
  const isArray = /\[.*\]/g.test(arrstr);
  if (isArray) {
    return JSON.parse(arrstr);
  }
  return [arrstr];
};