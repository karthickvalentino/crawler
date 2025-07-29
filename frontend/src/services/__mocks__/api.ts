export const getJobs = jest.fn(() => Promise.resolve([]));
export const getJob = jest.fn(() => Promise.resolve({ id: '1', status: 'completed', parameters: { domain: 'example.com' } }));
export const startCrawler = jest.fn(() => Promise.resolve({ id: '1' }));
export const stopCrawler = jest.fn(() => Promise.resolve({}));
export const deleteJob = jest.fn(() => Promise.resolve({}));
