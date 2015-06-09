module.exports = function(grunt) {

  grunt.initConfig({
    coffee: {
      src: {
        expand: true,
        cwd: 'src',
        src: '*.coffee',
        dest: 'lib',
        ext: '.js'
      }
    },

    browserify: {
      dist: {
        options: {

        },
        src: ['lib/startup.js'],
        dest: 'dist/livereload.js'
      }
    },

    mochaTest: {
      test: {
        options: {
          reporter: 'spec'
        },
        src: ['test/*.js']
      }
    }
  });

  grunt.loadNpmTasks('grunt-contrib-coffee');
  grunt.loadNpmTasks('grunt-browserify');
  grunt.loadNpmTasks('grunt-mocha-test');

  grunt.registerTask('build', ['coffee', 'browserify']);
  grunt.registerTask('test', ['mochaTest']);
  grunt.registerTask('default', ['build', 'test']);

};
