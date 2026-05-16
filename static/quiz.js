document.addEventListener('DOMContentLoaded', function () {
    var form = document.getElementById('quiz-all-form');
    if (!form) return;
    form.addEventListener('submit', function (e) {
        var questions = document.querySelectorAll('.quiz-question');
        var unanswered = [];

        questions.forEach(function (qDiv) {
            var radios = qDiv.querySelectorAll('input[type="radio"]');
            var answered = Array.from(radios).some(function (r) { return r.checked; });
            if (!answered) {
                qDiv.style.outline = '2px solid red';
                unanswered.push(qDiv.id);
            } else {
                qDiv.style.outline = '';
            }
        });

        if (unanswered.length > 0) {
            e.preventDefault();
            alert('還有 ' + unanswered.length + ' 題尚未作答，請完成所有題目後再送出。');
            document.getElementById(unanswered[0]).scrollIntoView({ behavior: 'smooth' });
        }
    });
});
