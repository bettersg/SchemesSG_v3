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