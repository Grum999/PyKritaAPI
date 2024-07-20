
function filterClear() {
    var classList = document.querySelectorAll('[data-version-first], [data-version-last]');

    for (index = 0; index < classList.length; index++) {
        var classItem = classList[index];

        classItem.classList.remove('hidden');
    }
}

function filterApply(version, delta) {
    var classList = document.querySelectorAll('[data-version-first], [data-version-last]');

    for (index = 0; index < classList.length; index++) {
        var classItem = classList[index],
            show = true;

        if (delta) {
            show = (version == classItem.getAttribute('data-version-first') ||
                    version == classItem.getAttribute('data-version-last')
                    );
        }
        else {
            show = (version == 'master' ||
                    classItem.getAttribute('data-version-first') <= version ||
                    classItem.getAttribute('data-version-last') <= version
                    );
        }

        if(show) {
            classItem.classList.remove('hidden');
        }
        else {
            classItem.classList.add('hidden');
        }
    }
}

window.addEventListener("message", (event) => {
    if (event.data.method == 'filterClear') {
        filterClear();
    }
    else if (event.data.method == 'filterApply') {
        filterApply(event.data.version, event.data.delta);
    }
});

document.addEventListener("readystatechange", (event) => {
    window.parent.postMessage({"method": "getFilter"}, "*");
});
