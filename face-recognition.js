/**
 * TORA FACE - Face Recognition Module
 * Handles photo upload, analysis, and results display
 */

class FaceRecognitionManager {
    constructor() {
        this.selectedFile = null;
        this.currentResults = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Upload area click
        const uploadArea = document.getElementById('upload-area');
        if (uploadArea) {
            uploadArea.addEventListener('click', () => {
                document.getElementById('photo-input').click();
            });

            // Drag and drop
            uploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadArea.classList.add('border-blue-500');
            });

            uploadArea.addEventListener('dragleave', () => {
                uploadArea.classList.remove('border-blue-500');
            });

            uploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadArea.classList.remove('border-blue-500');
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    this.handleFileSelect(files[0]);
                }
            });
        }

        // File input change
        const photoInput = document.getElementById('photo-input');
        if (photoInput) {
            photoInput.addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    this.handleFileSelect(e.target.files[0]);
                }
            });
        }

        // Analyze button
        const analyzeBtn = document.getElementById('analyze-btn');
        if (analyzeBtn) {
            analyzeBtn.addEventListener('click', () => this.analyzePhoto());
        }

        // Clear button
        const clearBtn = document.getElementById('clear-btn');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clearSelection());
        }

        // Export button
        const exportBtn = document.getElementById('export-btn');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => this.exportResults());
        }

        // New search button
        const newSearchBtn = document.getElementById('new-search-btn');
        if (newSearchBtn) {
            newSearchBtn.addEventListener('click', () => this.startNewSearch());
        }
    }

    handleFileSelect(file) {
        // Validate file type
        const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif'];
        if (!allowedTypes.includes(file.type)) {
            this.showError('Please select a valid image file (PNG, JPG, JPEG, GIF)');
            return;
        }

        // Validate file size (16MB max)
        const maxSize = 16 * 1024 * 1024;
        if (file.size > maxSize) {
            this.showError('File size must be less than 16MB');
            return;
        }

        this.selectedFile = file;
        this.showImagePreview(file);
    }

    showImagePreview(file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            const previewImg = document.getElementById('preview-img');
            previewImg.src = e.target.result;
            
            document.getElementById('upload-area').classList.add('hidden');
            document.getElementById('image-preview').classList.remove('hidden');
        };
        reader.readAsDataURL(file);
    }

    clearSelection() {
        this.selectedFile = null;
        document.getElementById('upload-area').classList.remove('hidden');
        document.getElementById('image-preview').classList.add('hidden');
        document.getElementById('results-section').classList.add('hidden');
        document.getElementById('photo-input').value = '';
    }

    async analyzePhoto() {
        if (!this.selectedFile) {
            this.showError('Please select a photo first');
            return;
        }

        if (!authManager.isAuthenticated()) {
            this.showError('Please log in to analyze photos');
            return;
        }

        try {
            this.showLoading(true);

            // Create form data
            const formData = new FormData();
            formData.append('image', this.selectedFile);
            formData.append('search_query', 'person face identification');

            // Send to backend
            const response = await fetch('/api/face/upload-and-analyze', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${authManager.getAuthToken()}`
                },
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                this.currentResults = data;
                this.displayResults(data);
                this.showSuccess('Analysis completed successfully!');
                this.updateSearchHistory();
            } else {
                throw new Error(data.error || 'Analysis failed');
            }

        } catch (error) {
            console.error('Analysis error:', error);
            this.showError(error.message || 'Error analyzing photo');
        } finally {
            this.showLoading(false);
        }
    }

    displayResults(data) {
        const resultsSection = document.getElementById('results-section');
        const faceAnalysis = document.getElementById('face-analysis');
        const searchResults = document.getElementById('search-results');

        // Display face analysis
        const attributes = data.primary_face.attributes;
        faceAnalysis.innerHTML = `
            <div class="bg-blue-50 rounded-lg p-4 mb-4">
                <h4 class="font-bold text-lg mb-3">Face Analysis</h4>
                <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div class="text-center">
                        <div class="text-2xl font-bold text-blue-600">${attributes.age || 'Unknown'}</div>
                        <div class="text-sm text-gray-600">Age</div>
                    </div>
                    <div class="text-center">
                        <div class="text-2xl font-bold text-blue-600">${attributes.gender || 'Unknown'}</div>
                        <div class="text-sm text-gray-600">Gender</div>
                    </div>
                    <div class="text-center">
                        <div class="text-2xl font-bold text-blue-600">${attributes.emotion || 'Unknown'}</div>
                        <div class="text-sm text-gray-600">Emotion</div>
                    </div>
                    <div class="text-center">
                        <div class="text-2xl font-bold text-blue-600">${data.faces_detected}</div>
                        <div class="text-sm text-gray-600">Faces Detected</div>
                    </div>
                </div>
            </div>
        `;

        // Display search results
        const totalMatches = data.search_results.total_matches;
        const googleImages = data.search_results.google_images || [];
        const socialProfiles = data.search_results.social_profiles || [];

        searchResults.innerHTML = `
            <div class="bg-green-50 rounded-lg p-4 mb-4">
                <h4 class="font-bold text-lg mb-3">
                    <i class="fas fa-search mr-2"></i>Search Results
                    <span class="text-sm font-normal text-gray-600">(${totalMatches} matches found)</span>
                </h4>
                
                ${googleImages.length > 0 ? `
                    <div class="mb-4">
                        <h5 class="font-semibold mb-2">Similar Images Found</h5>
                        <div class="grid grid-cols-2 md:grid-cols-4 gap-2">
                            ${googleImages.slice(0, 8).map(img => `
                                <div class="border rounded-lg p-2">
                                    <img src="${img.url}" alt="${img.alt_text}" class="w-full h-20 object-cover rounded">
                                    <p class="text-xs text-gray-600 mt-1 truncate">${img.alt_text || 'No description'}</p>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}

                ${socialProfiles.length > 0 ? `
                    <div class="mb-4">
                        <h5 class="font-semibold mb-2">Social Media Profiles</h5>
                        <div class="space-y-2">
                            ${socialProfiles.map(profile => `
                                <div class="border rounded-lg p-3 flex items-center justify-between">
                                    <div>
                                        <div class="font-medium">${profile.profile_name || 'Unknown'}</div>
                                        <div class="text-sm text-gray-600">${profile.platform} - ${profile.similarity_score}% match</div>
                                    </div>
                                    <a href="${profile.profile_url}" target="_blank" 
                                       class="text-blue-600 hover:text-blue-800">
                                        <i class="fas fa-external-link-alt"></i>
                                    </a>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}

                ${totalMatches === 0 ? `
                    <div class="text-center py-8 text-gray-500">
                        <i class="fas fa-search text-4xl mb-4"></i>
                        <p>No matches found in public databases</p>
                        <p class="text-sm">Try enhancing the image or using a different photo</p>
                    </div>
                ` : ''}
            </div>
        `;

        resultsSection.classList.remove('hidden');
    }

    async exportResults() {
        if (!this.currentResults) {
            this.showError('No results to export');
            return;
        }

        try {
            const response = await fetch('/api/face/export-results', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${authManager.getAuthToken()}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    search_results: this.currentResults,
                    case_number: prompt('Enter case number (optional):') || 'N/A'
                })
            });

            const data = await response.json();

            if (data.success) {
                // Create and download report
                this.downloadReport(data.report_data);
                this.showSuccess('Report exported successfully!');
            } else {
                throw new Error(data.error || 'Export failed');
            }

        } catch (error) {
            console.error('Export error:', error);
            this.showError('Error exporting results');
        }
    }

    downloadReport(reportData) {
        // Create a simple text report
        const reportText = `
TORA FACE - FACIAL RECOGNITION REPORT
=====================================

Officer Information:
- Badge Number: ${reportData.officer_info.badge_number}
- Department: ${reportData.officer_info.department}
- Country: ${reportData.officer_info.country}

Analysis Results:
- Faces Detected: ${reportData.search_results.faces_detected}
- Total Matches: ${reportData.search_results.search_results.total_matches}
- Analysis Date: ${new Date(reportData.export_timestamp).toLocaleString()}
- Case Number: ${reportData.case_number}

Face Attributes:
- Age: ${reportData.search_results.primary_face.attributes.age}
- Gender: ${reportData.search_results.primary_face.attributes.gender}
- Emotion: ${reportData.search_results.primary_face.attributes.emotion}

Search Results:
- Google Images: ${reportData.search_results.search_results.google_images.length} matches
- Social Profiles: ${reportData.search_results.search_results.social_profiles.length} profiles

Generated by TORA FACE Security System
        `;

        // Create and download file
        const blob = new Blob([reportText], { type: 'text/plain' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `TORA_FACE_Report_${Date.now()}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    }

    startNewSearch() {
        this.clearSelection();
        this.currentResults = null;
    }

    async updateSearchHistory() {
        try {
            const response = await fetch('/api/face/search-history?limit=5', {
                headers: {
                    'Authorization': `Bearer ${authManager.getAuthToken()}`
                }
            });

            const data = await response.json();

            if (data.success) {
                this.displaySearchHistory(data.history);
            }

        } catch (error) {
            console.error('Error updating search history:', error);
        }
    }

    displaySearchHistory(history) {
        const historyContainer = document.getElementById('search-history');
        
        if (history.length === 0) {
            historyContainer.innerHTML = '<p class="text-gray-500 text-center py-4">No recent searches</p>';
            return;
        }

        historyContainer.innerHTML = history.map(item => `
            <div class="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                <div>
                    <div class="font-medium">${item.search_type.replace('_', ' ').toUpperCase()}</div>
                    <div class="text-sm text-gray-600">
                        ${item.faces_detected} faces detected, ${item.matches_found} matches found
                    </div>
                </div>
                <div class="text-sm text-gray-500">
                    ${new Date(item.timestamp.seconds * 1000).toLocaleDateString()}
                </div>
            </div>
        `).join('');
    }

    showLoading(show) {
        const loading = document.getElementById('loading');
        const analyzeBtn = document.getElementById('analyze-btn');
        
        if (show) {
            loading.classList.remove('hidden');
            analyzeBtn.disabled = true;
            analyzeBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Analyzing...';
        } else {
            loading.classList.add('hidden');
            analyzeBtn.disabled = false;
            analyzeBtn.innerHTML = '<i class="fas fa-search mr-2"></i>Analyze Photo';
        }
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showNotification(message, type) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 p-4 rounded-lg text-white z-50 ${
            type === 'error' ? 'bg-red-500' : 'bg-green-500'
        }`;
        notification.innerHTML = `
            <div class="flex items-center">
                <i class="fas ${type === 'error' ? 'fa-exclamation-circle' : 'fa-check-circle'} mr-2"></i>
                <span>${message}</span>
            </div>
        `;

        document.body.appendChild(notification);

        // Remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
    }
}

// Initialize face recognition manager
const faceRecognitionManager = new FaceRecognitionManager();

