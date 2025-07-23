/**
 * Finance Tracker API Client
 * Provides functions to interact with the application's async API endpoints
 */

class FinanceTrackerAPI {
    /**
     * Initialize the API client
     * @param {Object} options - Configuration options
     */
    constructor(options = {}) {
        this.baseUrl = options.baseUrl || '';
        this.csrfToken = this.getCSRFToken();
    }
    
    /**
     * Get CSRF token from cookie
     * @returns {string} CSRF token
     */
    getCSRFToken() {
        // Get CSRF token from cookie
        const name = 'csrftoken=';
        const decodedCookie = decodeURIComponent(document.cookie);
        const cookieArray = decodedCookie.split(';');
        
        for (let i = 0; i < cookieArray.length; i++) {
            let cookie = cookieArray[i].trim();
            if (cookie.indexOf(name) === 0) {
                return cookie.substring(name.length, cookie.length);
            }
        }
        return '';
    }
    
    /**
     * Fetch transactions from the async API
     * @returns {Promise} Promise resolving to transaction data
     */
    async getTransactions() {
        try {
            const response = await fetch(`${this.baseUrl}/api/transactions/`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                },
                credentials: 'same-origin'
            });
            
            if (!response.ok) {
                throw new Error(`API error: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('Error fetching transactions:', error);
            throw error;
        }
    }
    
    /**
     * Fetch a single transaction by ID
     * @param {number} id - Transaction ID
     * @returns {Promise} Promise resolving to transaction data
     */
    async getTransaction(id) {
        try {
            const response = await fetch(`${this.baseUrl}/api/transactions/${id}/`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                },
                credentials: 'same-origin'
            });
            
            if (!response.ok) {
                throw new Error(`API error: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error(`Error fetching transaction ${id}:`, error);
            throw error;
        }
    }
}

// Example usage:
// const api = new FinanceTrackerAPI();
// api.getTransactions().then(data => {
//     console.log('Transactions:', data.transactions);
// });

// Make the API client available globally
window.FinanceTrackerAPI = FinanceTrackerAPI; 