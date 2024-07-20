
function filterClear() {
    var classList = document.querySelectorAll('li[data-version-first], li[data-version-last]');

    document.getElementById('iframeClass').contentWindow.postMessage({'method': 'filterClear'}, '*');

    for (index = 0; index < classList.length; index++) {
        var classItem = classList[index];

        classItem.classList.remove('hidden');
    }
}

function filterApply(version, delta) {
    var classList = document.querySelectorAll('li[data-version-first], li[data-version-last]');

    document.getElementById('iframeClass').contentWindow.postMessage({'method': 'filterApply', 'version': version, 'delta': delta}, '*');

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

document.addEventListener("readystatechange", (event) => {
    var selection = document.getElementById('tags'),
        viewModeDelta = document.getElementById('viewModeDelta'),
        viewModeDeltaLbl = document.getElementById('viewModeDeltaLbl'),
        update = function () {
            if (selection.value == 'master') {
                filterClear();
                //viewModeDelta.disabled = true;
                //viewModeDeltaLbl.classList.add('hidden');
                filterApply(selection.value, viewModeDelta.disabled == false && viewModeDelta.checked);
            }
            else {
                viewModeDelta.disabled = false;
                viewModeDeltaLbl.classList.remove('hidden');
                filterApply(selection.value, viewModeDelta.disabled == false && viewModeDelta.checked);
            }
        }

    selection.onchange = function (e) { update(); };
    viewModeDelta.onchange = function (e) { update(); };
});

window.addEventListener("message", (event) => {
    if (event.data.method == 'getFilter') {
        var selection = document.getElementById('tags');
        selection.onchange();
    }
});
