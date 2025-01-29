import axios from 'axios';

const api = axios.create({
    baseURL: `${import.meta.env.VITE_API_BASE_URL}`,
    withCredentials: true,
    headers: {
        'Content-Type': 'application/json'
    }
});

export const getCsrfToken = async () => {
    const response = await api.get('/auth/csrf-token');
    api.defaults.headers['X-CSRFToken'] = response.data.csrf_token;
};

export default api;