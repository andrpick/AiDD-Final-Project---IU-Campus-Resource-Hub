(function () {
    function init() {
        const rootElement = document.getElementById('featured-resources-root');
        if (!rootElement) {
            return;
        }

        const staticFallback = rootElement.querySelector('[data-static-render]');

        if (!(window.React && window.ReactDOM)) {
            console.warn('React is not available; skipping featured resources enhancement.');
            return;
        }

        const e = React.createElement;

        let resources = [];
        try {
            const raw = rootElement.dataset.resources || '[]';
            resources = JSON.parse(raw);
            if (!Array.isArray(resources)) {
                resources = [];
            }
        } catch (error) {
            console.error('Unable to parse featured resources payload.', error);
            resources = [];
        }

        const browseUrl = rootElement.dataset.browseUrl || '#';

        const formatCategory = (category) => {
            if (!category) {
                return 'Uncategorized';
            }
            return category
                .split('_')
                .filter(Boolean)
                .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
                .join(' ');
        };

        const hasCapacity = (value) => value !== null && value !== undefined && value !== '';

        function ResourceCard({ resource, view }) {
            const hasImage = Boolean(resource.image_url);
            const wrapperClasses = view === 'list'
                ? 'card-image-wrapper list-view-image-wrapper flex-shrink-0'
                : 'card-image-wrapper';

            const imageElement = hasImage
                ? e('img', {
                    src: resource.image_url,
                    alt: resource.title,
                    className: view === 'list'
                        ? 'w-100 h-100 object-fit-cover rounded-start'
                        : 'card-img-top'
                })
                : e(
                    'div',
                    {
                        className: 'featured-resource-placeholder d-flex align-items-center justify-content-center w-100 h-100',
                        role: 'img',
                        'aria-label': `No image available for ${resource.title}`
                    },
                    e('i', { className: 'bi bi-image', style: { fontSize: '3rem' } })
                );

            const metaRows = [];
            if (resource.location) {
                metaRows.push(
                    e(
                        'div',
                        { key: 'location', className: 'd-flex align-items-center gap-2 text-muted small' },
                        e('i', { className: 'bi bi-geo-alt text-crimson' }),
                        e('span', null, resource.location)
                    )
                );
            }
            if (hasCapacity(resource.capacity)) {
                metaRows.push(
                    e(
                        'div',
                        { key: 'capacity', className: 'd-flex align-items-center gap-2 text-muted small' },
                        e('i', { className: 'bi bi-people text-crimson' }),
                        e('span', null, `Capacity: ${resource.capacity}`)
                    )
                );
            }

            const categoryBadge = resource.category
                ? e(
                    'span',
                    { className: 'badge bg-crimson text-uppercase fw-semibold small' },
                    formatCategory(resource.category)
                )
                : null;

            const bodyChildren = [
                e('h5', { className: 'card-title mb-3' }, resource.title || 'Untitled Resource'),
                metaRows.length
                    ? e('div', { className: 'featured-resource-meta d-flex flex-column gap-1 mb-3' }, metaRows)
                    : null,
                categoryBadge ? e('div', { className: 'mb-3' }, categoryBadge) : null,
                e(
                    'a',
                    {
                        href: resource.detail_url || browseUrl,
                        className: 'btn btn-crimson mt-auto align-self-start'
                    },
                    'View Details'
                )
            ].filter(Boolean);

            const card = e(
                'div',
                { className: `card bg-white h-100${view === 'list' ? ' flex-row' : ''}` },
                [
                    e('div', { className: wrapperClasses }, imageElement),
                    e(
                        'div',
                        {
                            className: `card-body d-flex flex-column${view === 'list' ? ' flex-grow-1' : ''}`
                        },
                        bodyChildren
                    )
                ]
            );

            if (view === 'grid') {
                return e('div', { className: 'col-md-6 col-lg-4 col-xl-3 resource-card-wrapper d-flex' }, card);
            }

            return e('div', { className: 'featured-resources-list-item mb-3' }, card);
        }

        function FeaturedResourcesApp({ resources, browseUrl }) {
            const [searchTerm, setSearchTerm] = React.useState('');
            const [selectedCategory, setSelectedCategory] = React.useState('all');
            const [viewMode, setViewMode] = React.useState('grid');

            const normalizedSearch = searchTerm.trim().toLowerCase();

            const categories = React.useMemo(() => {
                const unique = new Set();
                resources.forEach((resource) => {
                    if (resource.category) {
                        unique.add(resource.category);
                    }
                });
                return Array.from(unique).sort((a, b) => formatCategory(a).localeCompare(formatCategory(b)));
            }, [resources]);

            const filteredResources = React.useMemo(() => {
                return resources
                    .filter((resource) => {
                        const matchesCategory =
                            selectedCategory === 'all' || resource.category === selectedCategory;
                        const matchesSearch =
                            !normalizedSearch ||
                            (resource.title && resource.title.toLowerCase().includes(normalizedSearch)) ||
                            (resource.location && resource.location.toLowerCase().includes(normalizedSearch));
                        return matchesCategory && matchesSearch;
                    })
                    .sort((a, b) => {
                        const titleA = (a.title || '').toLowerCase();
                        const titleB = (b.title || '').toLowerCase();
                        return titleA.localeCompare(titleB);
                    });
            }, [resources, normalizedSearch, selectedCategory]);

            const totalCount = resources.length;
            const filteredCount = filteredResources.length;
            const showClearFilters = normalizedSearch.length > 0 || selectedCategory !== 'all';

            const handleClearFilters = React.useCallback(() => {
                setSearchTerm('');
                setSelectedCategory('all');
            }, []);

            const searchField = e(
                'div',
                { className: 'flex-grow-1 position-relative featured-toolbar-search' },
                [
                    e('label', { className: 'form-label visually-hidden', htmlFor: 'featured-search-input' }, 'Search featured resources'),
                    e('i', { className: 'bi bi-search search-icon' }),
                    e('input', {
                        id: 'featured-search-input',
                        type: 'search',
                        className: 'form-control',
                        placeholder: 'Search by name or location…',
                        value: searchTerm,
                        onChange: (event) => setSearchTerm(event.target.value)
                    })
                ]
            );

            const categorySelect = categories.length
                ? e(
                    'div',
                    { className: 'featured-toolbar-select' },
                    [
                        e('label', { className: 'form-label visually-hidden', htmlFor: 'featured-category-select' }, 'Filter by category'),
                        e(
                            'select',
                            {
                                id: 'featured-category-select',
                                className: 'form-select',
                                value: selectedCategory,
                                onChange: (event) => setSelectedCategory(event.target.value)
                            },
                            [
                                e('option', { value: 'all' }, 'All categories'),
                                ...categories.map((category) =>
                                    e('option', { key: category, value: category }, formatCategory(category))
                                )
                            ]
                        )
                    ]
                )
                : null;

            const viewToggle = e(
                'div',
                { className: 'featured-toolbar-view-toggle ms-lg-auto' },
                [
                    e('span', { className: 'text-muted small me-2 d-none d-md-inline' }, 'View'),
                    e(
                        'div',
                        { className: 'btn-group view-toggle', role: 'group', 'aria-label': 'Toggle resource layout' },
                        [
                            e(
                                'button',
                                {
                                    type: 'button',
                                    className: `btn ${viewMode === 'grid' ? 'active' : ''}`,
                                    onClick: () => setViewMode('grid'),
                                    'aria-pressed': viewMode === 'grid'
                                },
                                [
                                    e('i', { className: 'bi bi-grid-fill me-2' }),
                                    'Grid'
                                ]
                            ),
                            e(
                                'button',
                                {
                                    type: 'button',
                                    className: `btn ${viewMode === 'list' ? 'active' : ''}`,
                                    onClick: () => setViewMode('list'),
                                    'aria-pressed': viewMode === 'list'
                                },
                                [
                                    e('i', { className: 'bi bi-list-ul me-2' }),
                                    'List'
                                ]
                            )
                        ]
                    )
                ]
            );

            const toolbarRows = [
                e(
                    'div',
                    { className: 'd-flex flex-column flex-lg-row align-items-lg-center gap-3 w-100' },
                    [searchField, categorySelect, viewToggle].filter(Boolean)
                )
            ];

            const summaryText = totalCount === 0
                ? 'No featured resources have been published yet.'
                : `Showing ${filteredCount} of ${totalCount} featured resources`;

            const summaryRowChildren = [
                e(
                    'div',
                    { className: 'featured-resources-summary text-muted small', 'aria-live': 'polite' },
                    summaryText
                )
            ];

            if (showClearFilters) {
                summaryRowChildren.push(
                    e(
                        'button',
                        {
                            type: 'button',
                            className: 'btn btn-link p-0 featured-resources-clear',
                            onClick: handleClearFilters
                        },
                        [e('i', { className: 'bi bi-arrow-counterclockwise me-1' }), 'Clear filters']
                    )
                );
            }

            toolbarRows.push(
                e(
                    'div',
                    { className: 'featured-toolbar-meta' },
                    summaryRowChildren
                )
            );

            const toolbar = e(
                'div',
                { className: 'featured-resources-toolbar' },
                toolbarRows
            );

            if (totalCount === 0) {
                return e(
                    React.Fragment,
                    null,
                    toolbar,
                    e(
                        'div',
                        { className: 'featured-resources-empty text-center p-4 mt-4' },
                        [
                            e('p', { className: 'mb-3 text-muted' }, 'No featured resources yet. Check back soon!'),
                            e(
                                'a',
                                { href: browseUrl, className: 'btn btn-outline-crimson' },
                                'Browse all resources'
                            )
                        ]
                    )
                );
            }

            if (filteredCount === 0) {
                return e(
                    React.Fragment,
                    null,
                    toolbar,
                    e(
                        'div',
                        { className: 'featured-resources-empty text-center p-4 mt-4' },
                        [
                            e('p', { className: 'mb-3 text-muted' }, 'No featured resources match your filters.'),
                            showClearFilters
                                ? e(
                                    'button',
                                    {
                                        type: 'button',
                                        className: 'btn btn-crimson',
                                        onClick: handleClearFilters
                                    },
                                    'Clear filters'
                                )
                                : null
                        ].filter(Boolean)
                    )
                );
            }

            const cards = filteredResources.map((resource) =>
                e(ResourceCard, {
                    key: resource.resource_id || resource.detail_url || resource.title,
                    resource,
                    view: viewMode
                })
            );

            const results = viewMode === 'grid'
                ? e('div', { className: 'row g-4 justify-content-center featured-resources-grid mt-4' }, cards)
                : e('div', { className: 'featured-resources-list mt-4' }, cards);

            return e(React.Fragment, null, toolbar, results);
        }

        const root = ReactDOM.createRoot
            ? ReactDOM.createRoot(rootElement)
            : null;
        const app = e(FeaturedResourcesApp, { resources, browseUrl });

        const markMounted = () => {
            rootElement.setAttribute('data-react-mounted', 'true');
        };

        if (root) {
            root.render(app);
            if (staticFallback) {
                (window.requestAnimationFrame || window.setTimeout)(markMounted);
            } else {
                markMounted();
            }
        } else if (ReactDOM.render) {
            ReactDOM.render(app, rootElement, () => {
                if (staticFallback) {
                    markMounted();
                } else {
                    markMounted();
                }
            });
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
