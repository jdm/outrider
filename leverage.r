data <- read.csv("leverage.csv",header=TRUE,sep=",")
ordered <- data[order(data$version),]
combined <- rbind(ordered$employees, ordered$volunteers)
svg("leverage.svg", width=7, height=7)
barplot(combined, names.arg=ordered$version, beside=TRUE, col=c("darkblue","lightblue"),
        legend=c("employees","volunteers"), xlab="Firefox release", ylab="Contributors",
        bty="n")
dev.off()
