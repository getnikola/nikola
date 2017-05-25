/* jshint node:true */

'use strict';

var gulp = require('gulp'),
    plugins = require('gulp-load-plugins')(),
    browserSync = require('browser-sync'),
    jsonfile = require('jsonfile'),
    runSequence = require('run-sequence');

var src = {
    css: ['./src/*.scss', './src/*.css'],
    js: './src/*.js'
};
var demo = {
    allFiles: './demo/**/*',
    css: './demo/css/',
    js: './demo/js/',
    html: './demo/',
    base: './demo/'
};
var dist = {
    css: './dist/',
    js: './dist/'
};

var autoprefixerBrowsers = [
    'last 2 version',
    '> 1%',
    'Edge >= 12',
    'Explorer >= 8',
    'Firefox 3.6',
    'Firefox ESR',
    'Opera 12.1'
];

gulp.task('build.demo-css', function() {
    return gulp.src(src.css)
        .pipe(plugins.if(/.scss/, plugins.sass({ style: 'compressed', noCache: true }))) // jshint ignore:line
        .pipe(plugins.autoprefixer(autoprefixerBrowsers))
        .pipe(plugins.concat('baguetteBox.css'))
        .pipe(gulp.dest(demo.css));
});

gulp.task('build.demo-js', function () {
    return gulp.src(src.js)
        .pipe(plugins.concat('baguetteBox.js'))
        .pipe(gulp.dest(demo.js));
});

gulp.task('build.dist-css', function() {
    return gulp.src(src.css)
        .pipe(plugins.if(/.scss/, plugins.sass({ style: 'compressed', noCache: true }))) // jshint ignore:line
        .pipe(plugins.autoprefixer(autoprefixerBrowsers))
        .pipe(plugins.concat('baguetteBox.css'))
        .pipe(gulp.dest(dist.css))
        .pipe(plugins.concat('baguetteBox.min.css'))
        .pipe(plugins.cssmin())
        .pipe(gulp.dest(dist.css));
});

gulp.task('build.dist-js', function() {
    return gulp.src(src.js)
        .pipe(plugins.concat('baguetteBox.js'))
        .pipe(gulp.dest(dist.js))
        .pipe(plugins.concat('baguetteBox.min.js'))
        .pipe(plugins.uglify({ preserveComments: 'some' }))
        .pipe(gulp.dest(dist.js));
});

gulp.task('build.demo', ['build.demo-css', 'build.demo-js']);

gulp.task('build.dist', ['build.dist-css', 'build.dist-js']);

gulp.task('lint', function() {
    return gulp.src([src.js, 'gulpfile.js'])
        .pipe(plugins.jshint())
        .pipe(plugins.jshint.reporter('jshint-stylish'))
        .pipe(plugins.jshint.reporter('fail'));
});

gulp.task('bump-minor', function () {
    return gulp.src(['./bower.json', './package.json'])
        .pipe(plugins.bump({ type: 'minor' }))
        .pipe(gulp.dest('./'));
});

gulp.task('bump-patch', function () {
    return gulp.src(['./bower.json', './package.json'])
        .pipe(plugins.bump({ type: 'patch' }))
        .pipe(gulp.dest('./'));
});

gulp.task('update-version', function () {
    return gulp.src([demo.css + '*.css',
            demo.js + '*.js',
            dist.css + '*.css',
            dist.js + '*.js'
        ], {
            base: './'
        })
        .pipe(plugins.injectVersion({
            replace: '%%INJECT_VERSION%%',
            prepend: ''
        }))
        .pipe(gulp.dest('./'));
});

gulp.task('watch', ['watch.browser-sync'], function() {
    gulp.watch(src.css, ['build.demo-css']);
    gulp.watch(src.js, ['build.demo-js', 'lint']);
});

gulp.task('watch.browser-sync', ['build.demo'], function () {
    var files = [
        demo.html + '*.html',
        demo.css + '*.css',
        demo.js + '*.js'
    ];

    browserSync.init(files, {
        server: {
            baseDir: demo.base
        }
    });
});

gulp.task('deploy', function() {
    var packageJson = jsonfile.readFileSync('./package.json');

    return gulp.src(demo.allFiles)
        .pipe(plugins.ghPages({
            push: false,
            message: 'v' + packageJson.version
        }));
});

gulp.task('release', function() {
    runSequence('bump-minor', 'build');
});

gulp.task('patch', function() {
    runSequence('bump-patch', 'build');
});

gulp.task('build', function() {
    runSequence(['build.demo', 'build.dist'], 'update-version');
});

gulp.task('test', ['build', 'lint']);

gulp.task('default', ['watch']);
